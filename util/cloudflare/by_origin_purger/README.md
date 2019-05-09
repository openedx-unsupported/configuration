
Cloudflare cache keys include the origin, so in order to purge assets with cached CORS headers you need to 
purge cloudflare cache assets by origin



build target list like so:
aws s3 ls s3://edx-course-videos/HarvardMed --recursive | awk '{print $4}' > targets

Make sure this seems reasonable...
cat targets
cat targets | wc -l

    python purger.py --origin https://cmeonline.hms.harvard.edu --cloudflare_site_url https://edx-video.net --target_path targets
    Will purge: https://edx-video.net/HarvardMedGlobalAcademyCCE-V000100/HarvardMedGlobalAcademyCCE-V000100.m3u8 at origin   https://cmeonline.hms.harvard.edu and 500 others like it. Add --confirm to execute.
    Will purge: https://edx-video.net/HarvardMedGlobalAcademySDM-V000400/HarvardMedGlobalAcademySDM-V000400_3_49.ts at origin   https://cmeonline.hms.harvard.edu and 500 others like it. Add --confirm to execute.
    Will purge: https://edx-video.net/HarvardMedGlobalAcademySDM-V000600/HarvardMedGlobalAcademySDM-V000600_5_13.ts at origin https://cmeonline.hms.harvard.edu and 500 others like it. Add --confirm to execute.
    Will purge: https://edx-video.net/HarvardMedGlobalAcademySDM-V000700/HarvardMedGlobalAcademySDM-V000700_6_46.ts at origin https://cmeonline.hms.harvard.edu and 500 others like it. Add --confirm to execute.
    Will purge: https://edx-video.net/HarvardMedGlobalAcademySDM-V001100/HarvardMedGlobalAcademySDM-V001100_1_5.ts at origin https://cmeonline.hms.harvard.edu and 500 others like it. Add --confirm to execute.
    Will purge: https://edx-video.net/HarvardMedGlobalAcademySDM-V001200/HarvardMedGlobalAcademySDM-V001200_6_1.ts at origin https://cmeonline.hms.harvard.edu and 500 others like it. Add --confirm to execute.
    Will purge: https://edx-video.net/HarvardMedGlobalAcademySDM-V001700/HarvardMedGlobalAcademySDM-V001700_2_11.ts at origin https://cmeonline.hms.harvard.edu and 500 others like it. Add --confirm to execute.
    Will purge: https://edx-video.net/HarvardMedGlobalAcademySDM-V001900/HarvardMedGlobalAcademySDM-V001900_6_12.ts at origin https://cmeonline.hms.harvard.edu and 500 others like it. Add --confirm to execute.
    Will purge: https://edx-video.net/HarvardMedGlobalAcademySDM-V002000/HarvardMedGlobalAcademySDM-V002000_6_28.ts at origin https://cmeonline.hms.harvard.edu and 51 others like it. Add --confirm to execute.

    python purger.py --origin https://cmeonline.hms.harvard.edu --cloudflare_site_url https://edx-video.net --target_path targets
    {'result': {'id': '5f6352f5511205f7ce2926fc6a90d669'}, 'success': True, 'errors': [], 'messages': []}
    {'result': {'id': '5f6352f5511205f7ce2926fc6a90d669'}, 'success': True, 'errors': [], 'messages': []}
    {'result': {'id': '5f6352f5511205f7ce2926fc6a90d669'}, 'success': True, 'errors': [], 'messages': []}
    {'result': {'id': '5f6352f5511205f7ce2926fc6a90d669'}, 'success': True, 'errors': [], 'messages': []}
    {'result': {'id': '5f6352f5511205f7ce2926fc6a90d669'}, 'success': True, 'errors': [], 'messages': []}
    {'result': {'id': '5f6352f5511205f7ce2926fc6a90d669'}, 'success': True, 'errors': [], 'messages': []}
    {'result': {'id': '5f6352f5511205f7ce2926fc6a90d669'}, 'success': True, 'errors': [], 'messages': []}
    {'result': {'id': '5f6352f5511205f7ce2926fc6a90d669'}, 'success': True, 'errors': [], 'messages': []}
    {'result': {'id': '5f6352f5511205f7ce2926fc6a90d669'}, 'success': True, 'errors': [], 'messages': []}
