# -*- coding: utf-8 -*-
from django.test import TestCase
from django.conf import settings
from models import Wikipage

setattr(settings, 'WIKIMEDIA_LANGUAGES', [('en', ''),('ru', '')])
delattr(settings, 'WIKIMEDIA_PARSER')

class WikimediaTestCase(TestCase):

    def test_import(self):
        '''Test of importing wikipedia page'''
        page1 = Wikipage.objects.update(u'Беспечный ездок', 'ru')

        self.assertEqual(Wikipage.objects.count(), 1)

        page2 = Wikipage.objects.latest()
        self.assertEqual(page1, page2)
        self.assertTrue(page2.content.find(u'художественный фильм') != -1)
        self.assertTrue(page2.content.find('<span lang="en" xml:lang="en">Easy Rider</span>') != -1)

    def test_import_unicode_symbols(self):

        page1 = Wikipage.objects.update(u'Mango_Soufflé', 'en')
        page2 = Wikipage.objects.update(u'Герой_(фильм,_2002)', 'ru')
        page3 = Wikipage.objects.update(u'Hero_(2002_film)', 'en')

        self.assertEqual(Wikipage.objects.count(), 3)
        self.assertTrue(page1.content.find(u'Mahesh Dattani') != -1)
        self.assertTrue(page2.content.find(u'英雄') != -1)
        self.assertTrue(page3.content.find(u'無名') != -1)

    def test_different_projects(self):
        '''
        Test importing content from different wikimedia projects
        '''
        page1 = Wikipage.objects.update(u'Father_Goose_(film)', 'en')
        page2 = Wikipage.objects.update(u'Father_Goose_(film)', 'en', 'wikipedia')
        page3 = Wikipage.objects.update(u'Father_Goose_(film)', 'en', 'wikiquote')

        self.assertEqual(page1, page2)
        self.assertEqual(Wikipage.objects.count(), 2)

        page4 = Wikipage.objects.update(u'Father_Goose_(film)', 'en', object=page3)
        self.assertEqual(Wikipage.objects.count(), 3)
        page4 = Wikipage.objects.update(u'Father_Goose_(film)', 'en', object=page4)
        self.assertEqual(Wikipage.objects.count(), 4)

    def test_parsing_chain_of_projects(self):
        '''
        Test of automatically parsing the chain of different wikimedia projects
        '''
        page = Wikipage.objects.update(u'Большой_Лебовски', 'ru', with_sister_projects=True)
        self.assertEqual(page.sister_projects, [('wikiquote', u'Большой_Лебовски')])
        self.assertEqual(Wikipage.objects.count(), 2)

        page1 = Wikipage.objects.get(project__code='wikiquote')
        self.assertTrue(page1.content.find(u'Ковер задавал стиль всей комнате') != -1)

        Wikipage.objects.all().delete()

        page = Wikipage.objects.update(u'Альберт_Эйнштейн', 'ru', with_sister_projects=True)
        self.assertEqual(page.sister_projects, [('wikiquote', u'Альберт_Эйнштейн'), ('wikicommons', u'Albert_Einstein')])
        self.assertEqual(Wikipage.objects.count(), 3)

        page1 = Wikipage.objects.get(project__code='wikiquote')
        page2 = Wikipage.objects.get(project__code='wikicommons')
        self.assertTrue(page1.content.find(u'Бог хитёр, но не злонамерен') != -1)
        self.assertTrue(page2.content.find(u'The oldest picture of Einstein') != -1)

        Wikipage.objects.all().delete()

        page = Wikipage.objects.update(u'Big_Lebowski', 'en', with_sister_projects=True)
        self.assertEqual(page.sister_projects, [('wikiquote', u'The_Big_Lebowski')])
        self.assertEqual(Wikipage.objects.count(), 2)

        page1 = Wikipage.objects.get(project__code='wikiquote')
        self.assertTrue(page1.content.find(u'The Dude abides') != -1)

        Wikipage.objects.all().delete()

        page = Wikipage.objects.update(u'Albert_Enstein', 'en', with_sister_projects=True)
        self.assertEqual(page.sister_projects, [
            ('wiktionary', u'Albert_Einstein'), # bad
            ('wikicommons', u'Albert_Einstein'),
            ('wikiversity', u'Albert_Einstein'),
            ('wikinews', u'Albert_Einstein'), # bad
            ('wikiquote', u'Albert_Einstein'),
            ('wikisource', u'Author:Albert_Einstein'),
            ('wikibooks', u'Albert_Einstein'), # bad
        ])
        self.assertEqual(Wikipage.objects.count(), 5)

    def test_removing_garbage(self):
        '''Test of importing wikipedia page'''
        ru = Wikipage.objects.update(u'Беспечный ездок', 'ru')
        en = Wikipage.objects.update(u'Easy rider', 'en')

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

        ru = Wikipage.objects.update(u'Большой_Лебовски', 'ru')
        self.assertTrue(ru.content.find(u'<dt>Литература</dt>') == -1)
        self.assertTrue(ru.content.find(u'style="') == -1)
        self.assertTrue(ru.content.find(u'bgcolor="') == -1)
        self.assertTrue(ru.content.find(u'class="') == -1)
        self.assertTrue(ru.content.find(u'<script') == -1)

        ru = Wikipage.objects.update(u'Аватар_(фильм,_2009)', 'ru')
        self.assertTrue(ru.content.find(u'Не следует путать') == -1)

        ru = Wikipage.objects.update(u'Список_Шиндлера', 'ru')
        self.assertTrue(ru.content.find(u'Это статья о фильме. О соответствующих реальных событиях см. статью') == -1)

        ru = Wikipage.objects.update(u'Король_говорит!', 'ru')
        self.assertTrue(ru.content.find(u'ogg_player_1') == -1)

        ru = Wikipage.objects.update(u'Револьвер_(фильм)', 'ru')
        self.assertTrue(ru.content.find(u'ogg_player_1') == -1)
        self.assertTrue(ru.content.find(u'По словам режиссёра Гая Ричи') != -1)

        ru = Wikipage.objects.update(u'Титаник_(фильм,_1997)', 'ru')
        self.assertTrue(ru.content.find(u'См. также') == -1)