#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import logging


def print_approach_title(title):
    logging.info('-' * 37)
    logging.info('- %s' % title)
    logging.info('-' * 37)


def replace_html_entity(data):
    return data.replace("&", "&amp;")\
        .replace("<", "&lt;")\
        .replace(">", "&gt;")\
        .replace("\n", "<br>")\
        .replace(" ", "&nbsp;")
