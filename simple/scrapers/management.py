# encoding: utf-8
from okscraper_django.management.base_commands import NoArgsDbLogCommand
from optparse import make_option


class BaseKnessetDataserviceCommand(NoArgsDbLogCommand):
    """
    A base command to ease fetching the data from the knesset API into the app schema

    """

    _DS_TO_APP_KEY_MAPPING = tuple()
    _DS_CONVERSIONS = {}

    def _has_existing_object(self, dataservice_object):
        raise NotImplementedError()

    def _create_new_object(self, dataservice_object):
        raise NotImplementedError()

    def recreate_objects(self, object_ids):
        raise NotImplementedError()

    def _translate_ds_to_model(self, ds_meeting):
        """
        The function provide a mapping service from knesset-data data structure to the app schema using
        the `translate_ds_to_model` . In order to use, fill the `_DS_TO_APP_KEY_MAPPING` and
        `_DS_CONVERSIONS` in the inheriting class in the following manner:

            _DS_TO_APP_KEY_MAPPING = ((app_key, knesset_data_key),(app_key, knesset_data_key)...)
            _DS_CONVERSIONS = {app_key: conversion_fn, ...}

        This will take the attributes from the knesset-data class and will yield a key, value tuples
        with the new key and the value conversion (if any).

        :param ds_meeting: The knesset data service class
        """
        for model_key, ds_key in self._DS_TO_APP_KEY_MAPPING:
            val = getattr(ds_meeting, ds_key)
            if model_key in self._DS_CONVERSIONS:
                val = self._DS_CONVERSIONS[model_key](val)
            yield model_key, val


class ReachedMaxItemsException(Exception):
    pass


class BaseKnessetDataserviceCollectionCommand(BaseKnessetDataserviceCommand):
    DATASERVICE_CLASS = None

    option_list = BaseKnessetDataserviceCommand.option_list + (
        make_option('--page-range', dest='pagerange', default='1-10',
                    help="range of page number to scrape (e.g. --page-range=5-12), default is 1-10"),
        make_option('--max-items', dest='maxitems', default='0',
                    help='maximum number of items to process'),
        make_option('--re-create', dest='recreate', default='',
                    help='comma-separated item ids to delete and then re-create'),
    )

    def _handle_page(self, page_num):
        for dataservice_object in self.DATASERVICE_CLASS.get_page(page_num=page_num):
            if not self._has_existing_object(dataservice_object):
                object = self._create_new_object(dataservice_object)
                self._log_debug(u'created new object %s: %s' % (object.pk, object))
                if self._max_items > 0:
                    self._num_items += 1
                    if self._num_items == self._max_items:
                        raise ReachedMaxItemsException('reached maxitems')

    def _handle_noargs(self, **options):
        if (options['recreate'] != ''):
            self._log_info('recreating objects %s' % options['recreate'])
            recreated_objects = self.recreate_objects(
                [int(id) for id in options['recreate'].split(',')])
            self._log_info(
                'created as objects %s' % (','.join([str(o.pk) for o in recreated_objects]),))
        else:
            page_range = options['pagerange']
            first, last = map(int, page_range.split('-'))
            self._max_items = int(options['maxitems'])
            self._num_items = 0
            for page_num in range(first, last + 1):
                self._log_debug('page %s' % page_num)
                try:
                    self._handle_page(page_num)
                except ReachedMaxItemsException:
                    break
