# -*- coding: utf-8 -*-
"""
Verifies that an index was correctly copied from one ES host to another.
"""

from __future__ import absolute_import
from __future__ import print_function
import itertools
import pprint
import random

from deepdiff import DeepDiff
from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan
from argparse import ArgumentParser


description = """
Compare two Elasticsearch indices
"""

SCAN_ITER_STEP = 50
SCAN_MATCH_THRESHOLD = .9

RANDOM_CHECK_SIZE = 10
RANDOM_CHECKS_BEFORE_RESET = 100

def parse_args():
    """
    Parse the arguments for the script.
    """
    parser = ArgumentParser(description=description)

    parser.add_argument(
        '-o', '--old', dest='old', required=True, nargs=2,
        help='Hostname and index of old ES host, e.g. https://localhost:9200 content'
    )
    parser.add_argument(
        '-n', '--new', dest='new', required=True, nargs=2,
        help='Hostname of new ES host, e.g. https://localhost:9200 content'
    )
    parser.add_argument(
        '-s', '--scan', dest='scan', action="store_true",
        help='Run a full scan comparison instead of a random selection.'
    )
    parser.add_argument(
        '-c', '--check-percentage', dest='check_percentage', type=float, default=.1,
        help='Percentage of randomly found docs to check between old and new indices (default: .1)'
    )

    return parser.parse_args()


def grouper(iterable, n):
    """
    Collect data into fixed-length chunks or blocks
    from the import itertools recipe list: https://docs.python.org/3/library/itertools.html#recipes
    """
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args)


def docs_match(old_doc, new_doc):
    """
    Return True if the the docs match, minus the ignorable fields

    Args:
        old_doc: a dict of an elasticsearch doc from the old cluster
        new_doc: a dict of an elasticsearch doc from the new cluster
    """
    """
    example doc:
    {'dictionary_item_added': {
        "root['_source']['_id']",
        "root['_source']['abuse_flaggers']",
        "root['_source']['anonymous']",
        "root['_source']['anonymous_to_peers']",
        "root['_source']['at_position_list']",
        "root['_source']['author_username']",
        "root['_source']['closed']",
        "root['_source']['comment_count']",
        "root['_source']['historical_abuse_flaggers']",
        "root['_source']['pinned']",
        "root['_source']['thread_type']",
        "root['_source']['visible']",
        "root['_source']['votes']",
        "root['found']"},
     'dictionary_item_removed': {
        "root['_source']['id']",
        "root['_source']['thread_id']",
        "root['_source']['votes_point']",
        "root['exists']"},
     'values_changed': {
        "root['_index']": {
            'new_value': u'content_20170324145539907',
            'old_value': u'content_20151207225034'},
        "root['_source']['body']": {
            'new_value': u'encryption neglect hypothesize polluters wining pitiably prophetess apostrophe foretelling assignments diaphragms trustees scroll scruffs shrivels characterizes digraph lasted sharked rewind chamoix charier protoplasm rapports isolated upbraid mortgaged cuddled indefinitely sinful insaner slenderized cemetery deject soundly preventable',
            'old_value': u'embellishing orbitals complying alternation welching sepulchered grate blench placenta landslide dependance hurdle predicted chaplet earsplitting assess awol necrosis freeways skipper delicatessen sponsorship bellboys antiseptics gabardines admittedly screechier professional roughness educations nutting valences iridescence deductions'},
        "root['_source']['title']": {
            'new_value': u'southpaw afterward playgoers roughed requites arrived byplay ninetieth textural rental foreclosing',
            'old_value': u'guttersnipes corduroys ghostly discourtesies'},
        "root['_source']['updated_at']": {
            'new_value': u'2017-03-29T18:51:19Z',
            'old_value': u'2017-03-28T12:58:02Z'},
        "root['_version']": {
            'new_value': 20,
            'old_value': 1}}}
"""
    ignorable_fields = [
        "root['exists']",
        "root['found']",
        "root['_index']",
        "root['updated_at']",
        "root['_version']",
        "root['_score']",
    ]
    diff_types = ['dictionary_item_added', 'dictionary_item_removed', 'values_changed']
    diff_doc = DeepDiff(old_doc, new_doc)

    if 'values_changed' not in diff_doc:
        diff_doc['values_changed'] = set()

    #if this fails something is horribly wrong
    if set(diff_doc.keys()) != set(diff_types):
        print('ERROR: expected to be diffing dictionaries, got something else! id: {}'.format(
            new_doc['_id']))

    for diff_type in diff_types:
        for field in ignorable_fields:
            if diff_type in diff_doc:
                #values_changed is a set, the other two are dicts
                if isinstance(diff_doc[diff_type], set):
                    diff_doc[diff_type].discard(field)
                else:
                    diff_doc[diff_type].pop(field, None)

    return all(len(diff_doc[diff_type]) == 0 for diff_type in diff_types)


def find_matching_ids(es, index, ids, docs):
    """
    Finds out how many of the ids in the given ids are in the given index in the given
    ES deployment.

    We also compare documents to ensure that those still match, skipping a few fields
    (see docs_match() for which ones).

    Args:
        es - Elasticsearch instance corresponding to the cluster we want to check
        index - name of the index that we want to check
        ids - a list of dictionaries of the form {'_id': <id>} of the ids we want to check.
        docs - a dictionary of the form {'<id>': document}, where "document"s are full ES docs
    """
    body = {'docs': ids}

    search_result = es.mget(index=index, body=body)
    matching = 0
    for elt in search_result['docs']:
        # Checks whether or not there was a document matching the id at all.
        # 'exists' is 0.9.x
        # 'found' is 1.5.x
        if elt.get('exists', False) or elt.get('found', False):
            if docs_match(docs[elt['_id']], elt):
                matching += 1
            else:
                print('FAILURE: Documents with id {id} do not match: '.format(
                    id=elt['_id']
                ) + repr({'diff': DeepDiff(docs[elt['_id']], elt), 'new': elt, 'old': docs[elt['_id']]}))
        else:
            print('ERROR: Document with id {id} missing: {doc}'.format(
                id=elt['_id'], doc=docs[elt['_id']]
            ))
    return matching


def scan_documents(old_es, new_es, old_index, new_index):
    """
    Scan for matching documents

     In order to match the two indices without having to deal with ordering issues,
     we pull a set of documents from the old ES index, and then try to find matching
     documents with the same _id in the new ES index. This process is batched to avoid
     making individual network calls to the new ES index.
    """

    matching = 0
    total = 0
    old_iter = scan(old_es, index=old_index)
    for old_elts in grouper(old_iter, SCAN_ITER_STEP):

        old_elt_ids = []
        old_elt_docs = {}
        for elt in old_elts:
            if elt is not None:
                old_elt_ids.append({'_id': elt['_id']})
                old_elt_docs[elt['_id']] = elt

        matching += find_matching_ids(new_es, new_index, old_elt_ids, old_elt_docs)
        total += len(old_elt_ids)
        if total % 100 == 0:
            print('processed {} items'.format(total))

    ratio = float(matching)/total
    print("{}: scanned documents matching ({} out of {}, {:.6}%)".format(
        'OK' if ratio > SCAN_MATCH_THRESHOLD else 'FAILURE', matching, total, ratio * 100
    ))


def random_checks(old_es, new_es, old_index, new_index, total_document_count, check_percentage):
    """
    Check random documents
    This is meant to be a random search trying to spot checks on whether
    or not data was moved over correctly. Runs a lot faster than the full scan.
    """

    total = 0
    matching = 0
    current_offset = -1
    while float(total) / total_document_count < check_percentage:
        # We only want to page a certain amount before regenerating a new set of
        # random documents.
        if current_offset > RANDOM_CHECKS_BEFORE_RESET or current_offset < 0:
            seed = random.randint(0, 1000)
            current_offset = 0
            body = {
                'size': RANDOM_CHECK_SIZE,
                'from': current_offset,
                'query': {
                    'function_score': {
                        'functions': [{
                            'random_score': {
                                'seed': seed
                            }
                        }]
                    }
                }
            }
        results = old_es.search(
            index=old_index, body=body
        )
        ids = []
        docs = {}
        for elt in results['hits']['hits']:
            ids.append({'_id': elt['_id']})
            docs[elt['_id']] = elt
        matching += find_matching_ids(new_es, new_index, ids, docs)
        num_elts = len(ids)
        total += num_elts
        current_offset += num_elts

        if total % 100 == 0:
            print('processed {} items'.format(total))

    ratio = float(matching) / total
    print("{}: random documents matching ({} out of {}, {}%)".format(
        'OK' if ratio > SCAN_MATCH_THRESHOLD else 'FAILURE', matching, total, int(ratio * 100)
    ))


def check_mappings(old_mapping, new_mapping):
    """
    Verify that the two mappings match in terms of keys and properties
    Args:
        - old_mapping (dict) - the mappings from the older ES
        - new_mapping(dict) - the mappings from the newer ES
    """

    deep_diff = DeepDiff(old_mapping, new_mapping)
    if deep_diff != {}:
        print("FAILURE: Index mappings do not match")
        pprint.pprint(deep_diff)
    else:
        print("OK: Index mappings match")


def main():
    """
    Run the verification.
    """
    args = parse_args()
    old_es = Elasticsearch([args.old[0]])
    new_es = Elasticsearch([args.new[0]])

    old_index = args.old[1]
    new_index = args.new[1]

    old_stats = list(old_es.indices.stats(index=old_index)['indices'].values())[0]['primaries']
    new_stats = list(new_es.indices.stats(index=new_index)['indices'].values())[0]['primaries']

    #compare document count
    old_count = old_stats['docs']['count']
    new_count = new_stats['docs']['count']

    print("{}: Document count ({} = {})".format(
        'OK' if old_count == new_count else 'FAILURE', old_count, new_count
    ))

    old_size = old_stats['store']['size_in_bytes']
    new_size = new_stats['store']['size_in_bytes']
    print("{}: Index size ({} = {})".format(
        'OK' if old_count == new_count else 'FAILURE', old_size, new_size
    ))

    def get_mappings(es, index):
        # for 1.5.x, there is an extra 'mappings' field that holds the mappings.
        mappings = list(es.indices.get_mapping(index=index).values())[0]
        new_style = mappings.get('mappings', None)
        return new_style if new_style is not None else mappings

    # Verify that the mappings match between old and new
    old_mapping = get_mappings(old_es, old_index)
    new_mapping = get_mappings(new_es, new_index)

    check_mappings(old_mapping, new_mapping)

    if args.scan:
        scan_documents(old_es, new_es, old_index, new_index)
    else:
        random_checks(old_es, new_es, old_index, new_index, new_count, args.check_percentage)



"""
index.stats()
elasticsearch.scroll()
use without scan during downtime
elasticsearch.helpers.scan is an iterator (whew)

sample first, then full validation
  is old subset of new?
  is number of edits small?

no numeric ids
can use random scoring?
{"size": 1, "query": {"function_score": {"functions":[{"random_score": {"seed": 123456}}]}}}
use that with scroll and check some number
can't use scroll with sorting. Maybe just keep changing the seed?
  It's kinda slow, but probably fine
  get `size` at a time
  are random sorts going to get the same docs on both clusters?
Alternative: random score with score cutoff? Or script field and search/cutoff
  Might also be able to use track_scores with scan&scroll on 1.5 and a score cutoff
"""

if __name__ == '__main__':
    main()
