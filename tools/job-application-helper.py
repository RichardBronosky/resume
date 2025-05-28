#!/usr/bin/env python3

import os
import argparse
import types
from datetime import datetime
from pprint import pprint

import pyperclip
import termcolor
import textwrap
import yaml

context = types.SimpleNamespace()

def setup():
    parser = argparse.ArgumentParser("job-application-helper.py")
    parser.add_argument("resume_file", help="Path to yaml file to be read.", type=argparse.FileType("r"))
    return parser.parse_args()

def indent(str, count=4):
    chars=' ' * count
    return "\n".join([f"{chars}{l}" if l.strip() else l for l in str.split('\n')])

def load(fd):
    iter_resume = yaml.safe_load_all(fd)
    # PEP 448
    *_, resume = iter_resume
    return resume

def copy(key, value):
    #disp = "\n".join(indent(value))
    disp = indent(value)
    if key in ['startDate', 'endDate']:
        try:
            month = datetime.strptime(value, '%Y-%m-%d').strftime('%b %Y')
            disp = f"{disp} ({month})"
        except ValueError:
            pass
    termcolor.cprint(f"Copied {key}:", "cyan")
    termcolor.cprint(f"{disp}", "magenta")
    pyperclip.copy(value)

def wait(msg):
    input(f"Next: {msg} (Press Enter)...")
    pass

def handle_work(work):
    for attr in ['position', 'name', 'startDate', 'endDate']:
        wait(attr)
        copy(attr, work.get(attr, ''))
    #breakpoint()
    desc = work.get('summary', '')
    if (len(desc) > 0):
        desc = f"{desc}\n\n"
    desc = (
            desc +
            str("\n".join([f"- {h}" for h in work.get('highlights', [])]))
            )
    wait('description')
    copy('description', desc)

def main():
    context.args=setup()
    context.resume = load(context.args.resume_file)
    context.index = os.environ.get('WORK_START_INDEX', '0')
    context.num = os.environ.get('WORK_START_NUM', '1')
    loop_index = 0
    for work in context.resume['work']:
        if loop_index < int(context.index):
            next
        loop_label = loop_index + int(context.num)
        pprint([f'Experience #{loop_label}', work])
        handle_work(work)
        #handle_work(types.SimpleNamespace(**context.resume['work'][0]))
        loop_index += 1

def test():
    with open('src/bruno.bronosky.resume.yaml', 'r') as fd:
        context.resume = load(fd)

if __name__ == "__main__":
    main()
