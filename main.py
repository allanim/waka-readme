'''
WakaTime progress visualizer
'''

import re
import os
import base64
import datetime
import pytz
import requests
from github import Github, GithubException


START_COMMENT = '<!--START_SECTION:waka-->'
END_COMMENT = '<!--END_SECTION:waka-->'
listReg = f"{START_COMMENT}[\\s\\S]+{END_COMMENT}"

user = os.getenv('INPUT_USERNAME')
waka_key = os.getenv('INPUT_WAKATIME_API_KEY')
ghtoken = os.getenv('INPUT_GH_TOKEN')

def make_graph(percent: float) -> str:
    '''Make progress graph from API graph'''
    done_block = '█'
    empty_block = '░'
    pc_rnd = round(percent)
    return f"{done_block*int(pc_rnd/4)}{empty_block*int(25-int(pc_rnd/4))}"


def make_list(data: list) -> str:
    '''Make List'''
    data_list = []
    for l in data[:5]:
        ln = len(l['name'])
        ln_text = len(l['text'])
        fmt_percent = format(l['percent'], '0.2f').zfill(5).rjust(6)+ ' %' # to provide a neat finish.
        data_list.append(
            f"{l['name']}{' '*(12-ln)}{l['text']}{' '*(20-ln_text)}{make_graph(l['percent'])}   {fmt_percent}"
        )
    return ' \n'.join(data_list)

def get_stats() -> str:
    '''Gets API data and returns markdown progress'''
    data = requests.get(
        f"https://wakatime.com/api/v1/users/current/stats/last_7_days?api_key={waka_key}").json()
    
    try:
        timezone = data['data']['timezone']
        start_date = data['data']['start']
        end_date = data['data']['end']
        lang_data = data['data']['languages']
        editor_data = data['data']['editors']
        os_data = data['data']['operating_systems']
    except KeyError:
        print("Please Add your Wakatime API Key to the Repository Secrets")
    
    offset = datetime.datetime.now(pytz.timezone(timezone)).utcoffset();
    start_tz = datetime.datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S%z') + offset
    end_tz = datetime.datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S%z') + offset
    duration = start_tz.strftime('%d %B, %Y') + ' - ' + end_tz.strftime('%d %B, %Y')

    lang_list = make_list(lang_data)
    editor_list = make_list(editor_data)
    os_list = make_list(os_data)

    return '```text\n📌 Timezone: '+timezone+'\n🔛 Duration: '+duration+'\n\n💬 Languages: \n'+lang_list+'\n\n🔥 Editors: \n'+editor_list+'\n\n💻 Operating Systems: \n'+os_list+'\n```'


def decode_readme(data: str) ->str:
    '''Decode the contets of old readme'''
    decoded_bytes = base64.b64decode(data)
    return str(decoded_bytes, 'utf-8')


def generate_new_readme(stats: str, readme: str) ->str:
    '''Generate a new Readme.md'''
    stats_in_readme = f"{START_COMMENT}\n{stats}\n{END_COMMENT}"
    return re.sub(listReg, stats_in_readme, readme)


if __name__ == '__main__':
    g = Github(ghtoken)
    try:
        repo = g.get_repo(f"{user}/{user}")
    except GithubException:
        print("Authentication Error. Try saving a GitHub Token in your Repo Secrets or Use the GitHub Actions Token, which is automatically used by the action.")
    contents = repo.get_readme()
    waka_stats = get_stats()
    print("---- Stats Generated ---")
    print(waka_stats)
    rdmd = decode_readme(contents.content)
    new_readme = generate_new_readme(stats=waka_stats, readme=rdmd)
    if new_readme != rdmd:
        repo.update_file(path=contents.path, message='Updated with Dev Metrics', content=new_readme, sha=contents.sha, branch='master')
