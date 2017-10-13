from bs4                             import BeautifulSoup
from selenium                        import webdriver
from selenium.webdriver.common.keys  import Keys
from urllib2                         import urlopen, URLError, HTTPError
from helper                          import *

import httplib
import cookielib
import json
import mechanize
import os
import time

# Constants
DATA_COURSE_LIST              = './DATA_COURSE_LIST.json'
DATA_COURSE_DETAILED_LIST_CDN = './DATA_COURSE_DETAILED_LIST_CDN.json'
URL_LOG_IN                    = 'https://frontendmasters.com/login/'
URL_COURSE_LIST               = 'https://frontendmasters.com/courses/'
BASE_URL                      = 'https://frontendmasters.com'

class Spider(object):
    def __init__(self):
        self.browser = webdriver.Chrome()

    def login(self, id, password):
        self.browser.get(URL_LOG_IN)
        time.sleep(2)

        username_field = self.browser.find_element_by_id('username')
        password_field = self.browser.find_element_by_id('password')

        username_field.send_keys(id)
        password_field.send_keys(password)
        password_field.send_keys(Keys.RETURN)

    def download(self, course):
        # Get detailed course list
        course_detailed_list = self._get_new_detailed_course_list(course)
        # Get downloadable CDN
        course_downloadbale = self._get_downloadable_links(course_detailed_list)

        

        # Download course videos
        self.download_course(course_downloadbale)

        # self.browser.close()
        
    def _get_new_detailed_course_list(self, course):
        course_link = URL_COURSE_LIST + course + '/'
        course_detial = {
            'title': course,
            'url': course_link,
            'sections': []
        }

        self.browser.get(course_link)
        self.browser.implicitly_wait(2)
        soup_page = BeautifulSoup(self.browser.page_source, 'html.parser')

        # Find video nav list
        all_items = soup_page.find('section', {'class': 'CourseToc'}).find('div', {'class': 's-wrap'}).select(' > *')
        sections = self._get_new_section_data(all_items)
        course_detial['sections'].extend(sections)

        return course_detial
        
        
    def _get_new_section_data(self, sections_items):
        sections = []
        for item in sections_items:
            # Course section data structure
            if item.name == 'h3':
                course_section = {
                    'title': '',
                    'subsections': []
                }
                course_section['title'] = item.getText()
                sections.append(course_section)
            elif item.name == 'ul':
                elements = item.find_all('a')
                sections_items = []
                for el in elements:
                    vid_link = el.get('href')
                    title = el.find('div', {'class': 'heading'}).find('h3').getText()
                    sections_items.append({
                        'title': title,
                        'url': vid_link,
                        'downloadable_url': None
                    })
                last_section_index = len(sections) - 1
                if last_section_index > -1:
                    sections[last_section_index]['subsections'] = sections_items

        sections.append(course_section)
        return sections

    def _get_downloadable_links(self, course):
        # course data structure
        # {
        #     'title': course,
        #     'url': course_link,
        #     'sections': []
        # }

        url = course['url']

        for section in course['sections']:
            for subsection in section['subsections']:
                if subsection['downloadable_url'] is None:
                    print("Retriving: {0}/{1}/{2}".format(
                        format_filename(course['title']),
                        format_filename(section['title']),
                        format_filename(subsection['title'])))

                    video_url = BASE_URL + subsection['url']
                    self.browser.get(video_url)
                    time.sleep(8)

                    url_str = self._get_video_source()
                    print("Video URL: {0}".format(url_str))
                    subsection['downloadable_url'] = url_str

        return course

    def _get_video_source(self):
        try:
            video_tag = self.browser.find_element_by_tag_name('video')
            source_link = video_tag.get_attribute('src')
            return source_link
        except:
            return "http://placehold.it/500x500"

    def download_course(self, course):
        # Create download directory
        create_path('./Download')
        title = course['title']

        # Create course directory
        course_path = './Download/{0}'.format(title)
        create_path(course_path)

        for i1, section in enumerate(course['sections']):
            section_title = section['title']
            
            # Create section directory
            section_path = './Download/{0}/{1} - {2}'.format(title, i1, section['title'])
            create_path(section_path)
            
            for i2, subsection in enumerate(section['subsections']):
                subsection_title = subsection['title']
                print("Downloading: {0}".format(
                    format_filename(subsection_title)))

                filename = str(i1) + '-' + str(i2) + ' ' + format_filename(subsection_title) + '.mp4'

                file_path = section_path + '/' + format_filename(filename)

                download_file(subsection['downloadable_url'], file_path, self)