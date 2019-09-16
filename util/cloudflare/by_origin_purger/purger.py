from __future__ import absolute_import
from __future__ import print_function
import requests
import click
from six.moves import range



def wrap(cloudflare_site_url, s3_asset_path, origin):
    url = str.format("{}/{}", cloudflare_site_url, s3_asset_path)
    return {
        "url": url,
        "headers": {
            "Origin": origin
        }
    }

def divide_chunks(list_to_divide, number_in_chunk): 
    for index in range(0, len(list_to_divide), number_in_chunk):  
        yield list_to_divide[index:index + number_in_chunk]

@click.command()
@click.option('--cloudflare_email', required=True, envvar='CLOUDFLARE_EMAIL')
@click.option('--cloudflare_api_key', required=True, envvar='CLOUDFLARE_API_KEY')
@click.option('--cloudflare_zone_id', required=True, envvar='CLOUDFLARE_ZONE_ID', help='Get this from the zones API endpoint')
@click.option('--origin', required=True)
@click.option('--cloudflare_site_url')
@click.option('--target_path', required=True)
@click.option('--confirm', is_flag=True)
def purge(cloudflare_email, cloudflare_api_key, cloudflare_zone_id, origin, cloudflare_site_url, target_path, confirm):
    with open(target_path) as f:
        lines = f.readlines()

    lines = [x.strip() for x in lines]
    for index, s3_asset_path in enumerate(lines):
        lines[index] = wrap(cloudflare_site_url, s3_asset_path, origin)

    chunk_size = 500
    chunks = divide_chunks(lines, chunk_size)
    for chunk in chunks:
        if not confirm:
            print((str.format("Will purge: {} at origin {} and {} others like it. Add --confirm to execute.", chunk[0]['url'], chunk[0]['headers']['Origin'], len(chunk))))
        else: 
            headers = {'X-Auth-Email': cloudflare_email,
                       'X-Auth-Key': cloudflare_api_key,
                       'Content-Type': 'application/json'}
            payload = {
                "files": chunk
            }
            url = str.format("https://api.cloudflare.com/client/v4/zones/{cloudflare_zone_id}/purge_cache", cloudflare_zone_id=cloudflare_zone_id)
            response = requests.delete(url, headers=headers, json=payload)
            print((response.json()))

if __name__ == '__main__':
    purge()
    
