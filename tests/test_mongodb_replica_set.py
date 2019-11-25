# Tests for mongodb_replica_set ansible module
#
# How to run these tests:
# 1. move this file to playbooks/library
# 2. rename mongodb_replica_set to mongodb_replica_set.py
# 3. python test_mongodb_replica_set.py

from __future__ import absolute_import
import mongodb_replica_set as mrs
import unittest, mock
from six.moves.urllib.parse import quote_plus
from copy import deepcopy

class TestNoPatchingMongodbReplicaSet(unittest.TestCase):
  def test_host_port_transformation(self):
    unfixed = {
      'members': [
        {'host': 'foo.bar'},
        {'host': 'bar.baz', 'port': 1234},
        {'host': 'baz.bing:54321'}
    ]}
    fixed = {
      'members': [
        {'host': 'foo.bar:27017'},
        {'host': 'bar.baz:1234'},
        {'host': 'baz.bing:54321'}
    ]}

    mrs.fix_host_port(unfixed)
    self.assertEqual(fixed, unfixed)

    fixed_2 = deepcopy(fixed)
    mrs.fix_host_port(fixed_2)
    self.assertEqual(fixed, fixed_2)

  def test_member_id_managed(self):
    new = [
        {'host': 'foo.bar', '_id': 1},
        {'host': 'bar.baz'},
        {'host': 'baz.bing'}
    ]
    old = [
      {'host': 'baz.bing', '_id': 0}
    ]

    fixed = deepcopy(new)
    mrs.set_member_ids(fixed, old)
    
    #test that each id is unique
    unique_ids = {m['_id'] for m in fixed}
    self.assertEqual(len(unique_ids), len(new))
    
    #test that it "prefers" the "matching" one in old_members
    self.assertEqual(fixed[0]['_id'], new[0]['_id'])
    self.assertEqual(fixed[2]['_id'], old[0]['_id'])
    self.assertIn('_id', fixed[1])

  def test_mongo_uri_escaped(self):
    host = username = password = auth_database = ':!@#$%/'
    port = 1234
    uri = mrs.get_mongo_uri(host=host, port=port, username=username, password=password, auth_database=auth_database)
    self.assertEqual(uri, "mongodb://{un}:{pw}@{host}:{port}/{db}".format(
      un=quote_plus(username), pw=quote_plus(password),
      host=quote_plus(host), port=port, db=quote_plus(auth_database),
    ))


rs_id = 'a replset id'
members = [
  {'host': 'foo.bar:1234'},
  {'host': 'bar.baz:4321'},
]
old_rs_config = {
  'version': 1,
  '_id': rs_id,
  'members': [
    {'_id': 0, 'host': 'foo.bar:1234',},
    {'_id': 1, 'host': 'bar.baz:4321',},
  ]
}
new_rs_config = {
  'version': 2,
  '_id': rs_id,
  'members': [
    {'_id': 0, 'host': 'foo.bar:1234',},
    {'_id': 1, 'host': 'bar.baz:4321',},
    {'_id': 2, 'host': 'baz.bing:27017',},
  ]
}
rs_config = {
  'members': [
    {'host': 'foo.bar', 'port': 1234,},
    {'host': 'bar.baz', 'port': 4321,},
    {'host': 'baz.bing', 'port': 27017,},
  ]
}

def init_replset_mock(f):
  get_replset_initialize_mock = mock.patch.object(mrs, 'get_replset', 
    side_effect=(None, deepcopy(new_rs_config)))
  initialize_replset_mock = mock.patch.object(mrs, 'initialize_replset')
  return get_replset_initialize_mock(initialize_replset_mock(f))
  
def update_replset_mock(f):
  get_replset_update_mock = mock.patch.object(mrs, 'get_replset', 
    side_effect=(deepcopy(old_rs_config), deepcopy(new_rs_config)))
  reconfig_replset_mock = mock.patch.object(mrs, 'reconfig_replset')
  return get_replset_update_mock(reconfig_replset_mock(f))

@mock.patch.object(mrs, 'get_rs_config_id', return_value=rs_id)
@mock.patch.object(mrs, 'client', create=True)
@mock.patch.object(mrs, 'module', create=True)
class TestPatchingMongodbReplicaSet(unittest.TestCase):
  
  @update_replset_mock
  def test_version_managed(self, _1, _2, module, *args):
    # Version set automatically on initialize
    mrs.update_replset(deepcopy(rs_config))
    new_version = module.exit_json.call_args[1]['config']['version']
    self.assertEqual(old_rs_config['version'], new_version - 1)

  @init_replset_mock
  def test_doc_id_managed_on_initialize(self, _1, _2, module, *args):
    #old_rs_config provided by init_replset_mock via mrs.get_replset().
    #That returns None on the first call, so it falls through to get_rs_config_id(),
    #which is also mocked.
    mrs.update_replset(deepcopy(rs_config))
    new_id = module.exit_json.call_args[1]['config']['_id']
    self.assertEqual(rs_id, new_id)

  @update_replset_mock
  def test_doc_id_managed_on_update(self, _1, _2, module, *args):
    #old_rs_config provided by update_replset_mock via mrs.get_replset()
    mrs.update_replset(deepcopy(rs_config))
    new_id = module.exit_json.call_args[1]['config']['_id']
    self.assertEqual(rs_id, new_id)

  @init_replset_mock
  def test_initialize_if_necessary(self, initialize_replset, _2, module, *args):
    mrs.update_replset(deepcopy(rs_config))
    self.assertTrue(initialize_replset.called)
    #self.assertFalse(reconfig_replset.called)

  @update_replset_mock
  def test_reconfig_if_necessary(self, reconfig_replset, _2, module, *args):
    mrs.update_replset(deepcopy(rs_config))
    self.assertTrue(reconfig_replset.called)
    #self.assertFalse(initialize_replset.called)

  @update_replset_mock
  def test_not_changed_when_docs_match(self, _1, _2, module, *args):
    rs_config = {'members': members}  #This way the docs "match", but aren't identical

    mrs.update_replset(deepcopy(rs_config))
    changed = module.exit_json.call_args[1]['changed']
    self.assertFalse(changed)

  @update_replset_mock
  def test_ignores_magic_given_full_doc(self, _1, _2, module, _3, get_rs_config_id, *args):
    mrs.update_replset(deepcopy(new_rs_config))
    new_doc = module.exit_json.call_args[1]['config']
    self.assertEqual(new_doc, new_rs_config)
    self.assertFalse(get_rs_config_id.called)


if __name__ == '__main__':
  unittest.main()
