
Cloudflare cache keys include the origin, so in order to purge assets with cached CORS headers you need to 
purge cloudflare cache assets by origin



build target list like so:
aws s3 ls s3://bucket-url/path --recursive | awk '{print $4}' > targets

Make sure this seems reasonable...
cat targets
cat targets | wc -l

    python purger.py --origin https://example.edu --cloudflare_site_url https://cloudflare-example.net --target_path targets
    Will purge: https://cloudflare-example.net/headerCCE-V230100/headerCCE-V230100.m3u8 at origin   https://example.edu and 500 others like it. Add --confirm to execute.
    Will purge: https://cloudflare-example.net/headerABC-V230400/headerABC-V230400_3_49.ts at origin   https://example.edu and 500 others like it. Add --confirm to execute.
    Will purge: https://cloudflare-example.net/headerABC-V230600/headerABC-V230600_5_13.ts at origin https://example.edu and 500 others like it. Add --confirm to execute.
    Will purge: https://cloudflare-example.net/headerABC-V230700/headerABC-V230700_6_46.ts at origin https://example.edu and 500 others like it. Add --confirm to execute.
    Will purge: https://cloudflare-example.net/headerABC-V231100/headerABC-V231100_1_5.ts at origin https://example.edu and 500 others like it. Add --confirm to execute.
    Will purge: https://cloudflare-example.net/headerABC-V231200/headerABC-V231200_6_1.ts at origin https://example.edu and 500 others like it. Add --confirm to execute.
    Will purge: https://cloudflare-example.net/headerABC-V231700/headerABC-V231700_2_11.ts at origin https://example.edu and 500 others like it. Add --confirm to execute.
    Will purge: https://cloudflare-example.net/headerABC-V231900/headerABC-V231900_6_12.ts at origin https://example.edu and 500 others like it. Add --confirm to execute.
    Will purge: https://cloudflare-example.net/headerABC-V232000/headerABC-V232000_6_28.ts at origin https://example.edu and 51 others like it. Add --confirm to execute.

    python purger.py --origin https://example.edu --cloudflare_site_url https://cloudflare-example.net --target_path targets
    {'result': {'id': 'BOSYunXGVf3uMevCy4J0Tk7AuuU849'}, 'success': True, 'errors': [], 'messages': []}
    {'result': {'id': 'BOSYunXGVf3uMevCy4J0Tk7AuuU849'}, 'success': True, 'errors': [], 'messages': []}
    {'result': {'id': 'BOSYunXGVf3uMevCy4J0Tk7AuuU849'}, 'success': True, 'errors': [], 'messages': []}
    {'result': {'id': 'BOSYunXGVf3uMevCy4J0Tk7AuuU849'}, 'success': True, 'errors': [], 'messages': []}
    {'result': {'id': 'BOSYunXGVf3uMevCy4J0Tk7AuuU849'}, 'success': True, 'errors': [], 'messages': []}
    {'result': {'id': 'BOSYunXGVf3uMevCy4J0Tk7AuuU849'}, 'success': True, 'errors': [], 'messages': []}
    {'result': {'id': 'BOSYunXGVf3uMevCy4J0Tk7AuuU849'}, 'success': True, 'errors': [], 'messages': []}
    {'result': {'id': 'BOSYunXGVf3uMevCy4J0Tk7AuuU849'}, 'success': True, 'errors': [], 'messages': []}
    {'result': {'id': 'BOSYunXGVf3uMevCy4J0Tk7AuuU849'}, 'success': True, 'errors': [], 'messages': []}
