# -*- coding: utf-8 -*-
from django.test import TestCase
from django.contrib.sites.models import Site
from models import WikipediaElement

class WikipediaTestCase(TestCase):

    def test_import(self):
        '''Test of importing wikipedia page'''
        object = Site.objects.create(domain='1', name='1')
        element1 = WikipediaElement.objects.update(object, 'ru', u'Беспечный ездок')

        self.assertEqual(WikipediaElement.objects.count(), 1)

        element2 = WikipediaElement.objects.all()[0]
        self.assertEqual(element1, element2)
        self.assertTrue(element2.content.find(u'художественный фильм') != -1)
        self.assertTrue(element2.content.find('<span lang="en" xml:lang="en">Easy Rider</span>') != -1)

    def test_import_unicode_symbols(self):

        object = Site.objects.create(domain='1', name='1')
        element1 = WikipediaElement.objects.update(object, 'en', u'Mango_Soufflé')
        element2 = WikipediaElement.objects.update(object, 'ru', u'Герой_(фильм,_2002)')
        element3 = WikipediaElement.objects.update(object, 'en', u'Hero_(2002_film)')

        self.assertEqual(WikipediaElement.objects.count(), 2)
        self.assertTrue(element1.content.find(u'Mahesh Dattani') != -1)
        self.assertTrue(element2.content.find(u'英雄') != -1)
        self.assertTrue(element3.content.find(u'無名') != -1)

    def test_removing_garbage(self):
        '''Test of importing wikipedia page'''
        object = Site.objects.create(domain='1', name='1')
        ru = WikipediaElement.objects.update(object, 'ru', u'Беспечный ездок')
        en = WikipediaElement.objects.update(object, 'en', u'Easy rider')

        self.assertTrue(ru.content.find(u'другие значения') == -1)
        self.assertTrue(en.content.find(u'disambiguation') == -1)
        self.assertTrue(ru.content.find(u'Постер фильма') == -1)
        self.assertTrue(en.content.find(u'Original poster') == -1)
        self.assertTrue(ru.content.find(u'<h2>Содержание</h2>') == -1)
        self.assertTrue(en.content.find(u'<h2>Contents</h2>') == -1)
        self.assertTrue(ru.content.find(u'Править секцию') == -1)
        self.assertTrue(en.content.find(u'Edit section') == -1)
        self.assertTrue(ru.content.find(u'<!-- Saved in parser cache') == -1)
        self.assertTrue(en.content.find(u'<!-- Saved in parser cache') == -1)
        self.assertTrue(en.content.find(u'metadata mbox-small plainlinks') == -1)
        self.assertTrue(ru.content.find(u'Ссылки') == -1)
        self.assertTrue(en.content.find(u'Links') == -1)
        self.assertTrue(ru.content.find(u'allmovie') == -1)
        self.assertTrue(ru.content.find(u'class="reference"') == -1)
        self.assertTrue(ru.content.find(u'Примечания') == -1)
        self.assertTrue(en.content.find(u'References') == -1)
        self.assertTrue(ru.content.find(u'The Road Movie Book') == -1)
        self.assertTrue(en.content.find(u'Internet Movie Database. Box office/Business for') == -1)

        ru = WikipediaElement.objects.update(object, 'ru', u'Большой_Лебовски')
        self.assertTrue(ru.content.find(u'<dt>Литература</dt>') == -1)
        self.assertTrue(ru.content.find(u'style="') == -1)
        self.assertTrue(ru.content.find(u'bgcolor="') == -1)
        self.assertTrue(ru.content.find(u'class="') == -1)
        self.assertTrue(ru.content.find(u'<script') == -1)

        ru = WikipediaElement.objects.update(object, 'ru', u'Аватар_(фильм,_2009)')
        self.assertTrue(ru.content.find(u'Не следует путать') == -1)

        ru = WikipediaElement.objects.update(object, 'ru', u'Список_Шиндлера')
        self.assertTrue(ru.content.find(u'Это статья о фильме. О соответствующих реальных событиях см. статью') == -1)

        ru = WikipediaElement.objects.update(object, 'ru', u'Король_говорит!')
        self.assertTrue(ru.content.find(u'ogg_player_1') == -1)

        ru = WikipediaElement.objects.update(object, 'ru', u'Титаник_(фильм,_1997)')
        self.assertTrue(ru.content.find(u'См. также') == -1)