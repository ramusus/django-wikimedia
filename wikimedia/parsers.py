# -*- coding: utf-8 -*-
from BeautifulSoup import BeautifulSoup, Comment, NavigableString
import re
import urllib


class WikipageGarbageRemove(object):

    '''
    Class for cleaning wikipage by removing unnecessary garbage
    '''
    table_classes = []  # table containers with specified class
    div_classes = []  # div containers with specified class
    span_classes = []  # span containers with specified class

    style_attribute = True  # attribute style from containers
    class_attribute = True  # attribute class from containers
    script = True  # scripts
    comments = True  # comments

    block_titles = []  # whole h2 blocks with specified title

    edit_links = True
    contents = True
    external_links = True
    external_links_titles = [u'Ссылки', 'links']
    infobox = True
    sisterproject = True
    navbox = True
    reference = True
    reference_links = True
    see_also = True
    disambiguation = True
    thumb_images = True
    audio = True


class WikipageParserBase(object):

    '''
    Common interface for wikipage parsers
    '''
    class Remove(WikipageGarbageRemove):
        pass

    content = None
    wikipage = None

    @property
    def remove(self):
        return self.Remove

    def process_content(self, content, wikipage):
        '''
        Process wikipedia content before saving to DB
        '''
        self.content = content
        self.wikipage = wikipage

        self.parse_content()
        self.remove_garbage()

        return self.content

    def parse_content(self):
        '''
        Parse wikipedia content page for useful information
        '''
        pass

    def remove_garbage(self):
        '''
        Remove unnecessary tags from wikipedia content page
        '''
        pass


class WikipageParserBeautifulsoup(WikipageParserBase):

    '''
    Wikipage parser based on BeautifulSoup library
    '''

    def process_content(self, content, wikipage):
        '''
        Process wikipedia content before saving to DB
        '''
        content = BeautifulSoup(content)
        content = super(WikipageParserBeautifulsoup, self).process_content(content, wikipage)
        content = unicode(content).strip()
        return content

    def parse_content(self):
        '''
        Parse wikipedia content for links to sister projects
        '''
        self.parse_sister_projects()

    def parse_sister_projects(self):
        '''
        Parse wikipedia content for links to sister projects
        '''
        self.wikipage.sister_projects = []  # important to make urls list empty
        project_urls = []
        projects = []

        registered_projects = self.wikipage.project.__class__.objects.all()

        for item in self.find_block_contents(self.remove.external_links_titles, remove_strings=True):

            # <table class="metadata plainlinks mbox-small"
            # <table class="metadata mbox-small plainlinks"
            # <table class="metadata plainlinks navigation-box"
            # <div class="infobox sisterproject noprint wikiquote-box"
            item_classes_set = set(item.get('class', '').split())
            if item.name == 'table' and set(['plainlinks']).issubset(item_classes_set) \
                    or item.name == 'div' and set(['infobox', 'sisterproject']).issubset(item_classes_set):

                if self.wikipage.lang == 'ru':
                    for link in item.findAll('span', {'class': re.compile('wikiquote-ref|wikicommons-ref')}):
                        project_urls += [link.find('a')['href']]

                elif self.wikipage.lang == 'en':
                    # http://en.wikiquote.org/wiki/Special:Search/The_Big_Lebowski
                    for link in item.findAll('a', {'href': re.compile('^(?:http:)?//.+\.org/wiki/'), 'class': re.compile('^(extiw|external text)$')}):
                        project_urls += [link['href']]

        # generate from found urls list with tuples (code, title)
        for url in project_urls:
            for domain, title in re.compile(r'^(?:http:)?//([^/]+)/wiki/(?:Special:Search/)?([^/\?]+)(?:\?.+)?$').findall(url):
                for project in registered_projects:
                    if domain == project.get_domain(self.wikipage.lang):
                        title = urllib.unquote(title.encode('utf-8')).decode('utf-8')
                        projects += [(project.code, title)]

        self.wikipage.sister_projects = projects

    def parse_wikicommons_images(self):
        '''
        Parse and return images from wikicommons wikimedia's project
        '''
        images = []
        for item in self.content.findAll('li', {'class': 'gallerybox'}):
            img = item.find('img')
            if not img:
                continue
            # http://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Einst_4.jpg/83px-Einst_4.jpg
            # //upload.wikimedia.org/wikipedia/commons/4/45/Einst_4.jpg
            image_url = re.sub(r'^(.+)thumb/(.+)/[^/]+', r'\1\2', img['src'])
            if image_url[0: 2] == '//':
                image_url = 'http:' + image_url
            try:
                image_text = unicode(item.find('div', {'class': 'gallerytext'}).find('p').contents[0])
            except:
                image_text = ''
            images += [(image_url, image_text)]

        return images

    def remove_garbage(self):
        '''
        Remove unnecessary tags from wikipedia content page
        '''
        table_classes = self.remove.table_classes
        div_classes = self.remove.div_classes
        span_classes = self.remove.span_classes

        # span editsection
        if self.remove.edit_links:
            [el.extract() for el in self.content.findAll('span', {'class': 'editsection'})]

        # table contents
        if self.remove.contents:
            [el.extract() for el in self.content.findAll('table', {'id': 'toc', 'class': 'toc'})]

        # scripts
        if self.remove.script:
            [el.extract() for el in self.content.findAll('script')]

        # remove all comments
        if self.remove.comments:
            [el.extract() for el in self.content.findAll(text=lambda text: isinstance(text, Comment))]

        # external links block (ru,en)
        if self.remove.external_links:
            self.remove.block_titles += self.remove.external_links_titles

        if self.remove.see_also:
            self.remove.block_titles += ['See also', u'См[^ ]+ также']

        if self.remove.reference_links:
            [el.extract() for el in self.content.findAll('sup', {'class': 'reference'})]

        if self.remove.reference:
            # references block (en) div class="reflist references-column-count references-column-count-2"
            div_classes += ['reflist', 'references-small']
            self.remove.block_titles += [u'Примечания', 'References', u'Источники', ]

        infobox = self.content.find(True, {'class': re.compile('infobox')})
        if infobox:
            if self.remove.disambiguation:
                [el.extract() for el in infobox.findAllPrevious(True)]
            if self.remove.infobox:
                infobox.extract()
                # sometimes there is another infoboxes on page http://ru.wikipedia.org/wiki/Король_говорит!
                table_classes += ['infobox']
                div_classes += ['infobox']

        if self.remove.sisterproject:
            # links to another wikimedia (en) table class="metadata mbox-small plainlinks"
            table_classes += ['metadata']
            # links to another wikimedia (ru) div class="infobox sisterproject noprint wikiquote-box"
            div_classes += ['sisterproject', 'wikiquote-box']

        if self.remove.navbox:
            # links to another movies of director table class="navbox collapsible autocollapse nowraplinks"
            table_classes += ['navbox', 'NavFrame']
            # links to another cities of this region
            table_classes += ['toccolours']
            div_classes += ['navbox', 'NavFrame']

        if self.remove.disambiguation:
            # disambiguation div class="dablink" (en)
            div_classes += ['dablink']

        if self.remove.thumb_images:
            div_classes += ['thumb']

        if self.remove.audio:
            set_parents = [el.findParents()[-2].extract()
                           for el in self.content.findAll('div', {'id': re.compile('^ogg_player_')})]
            span_classes += ['audiolink', 'audiolinkinfo']

        # lock icon (en) <div class="metadata topicon" id="protected-icon">
        [el.extract() for el in self.content.findAll('div', {'id': 'protected-icon'})]
        div_classes += ['metadata']

        [el.extract() for el in self.content.findAll('table', {'class': re.compile('(%s)' % '|'.join(table_classes))})]
        [el.extract() for el in self.content.findAll('div', {'class': re.compile('(%s)' % '|'.join(div_classes))})]
        [el.extract() for el in self.content.findAll('span', {'class': re.compile('(%s)' % '|'.join(span_classes))})]
        self.remove_blocks()

        # remove all style attributes
        if self.remove.style_attribute:
            for el in self.content.findAll(style=True):
                del el['style']
            for el in self.content.findAll(bgcolor=True):
                del el['bgcolor']

        if self.remove.class_attribute:
            for el in self.content.findAll(True, {'class': True}):
                del el['class']

    def remove_blocks(self):
        '''
        Remove h2 title and all next tags siblings until next h2 title
        '''
        [el.extract() for el in self.find_block_contents(self.remove.block_titles)]

    def find_block_contents(self, titles, remove_strings=False):
        '''
        Find and return all block items with h2 title and all next tags siblings until next h2 title
        '''
        items = []
        for title in self.content.findAll(text=re.compile(u'(%s)' % u'|'.join(titles))):
            # get h2
            title = title.findParent('h2')
            if not title:
                continue
            next = title.nextSibling

            if not isinstance(title, NavigableString) or not remove_strings:
                items += [title]

            while next and (isinstance(next, NavigableString) or next.name != 'h2'):

                if not isinstance(next, NavigableString) or not remove_strings:
                    items += [next]

                next = next.nextSibling

        return items
