
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
import quast_app
admin.autodiscover()

from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.conf import settings
from quast_app import views, login_views
from django.views.generic import TemplateView, RedirectView

import logging
logger = logging.getLogger('quast')


urlpatterns = patterns('',
    url(r'^robots\.txt$', RedirectView.as_view(url='/static/robots.txt')),
    url(r'^sitemap\.xml$', RedirectView.as_view(url='/static/sitemap.xml')),
    url(r'^excanvas\.min\.js$', RedirectView.as_view(url='/static/float/excanvas.min.js')),
    url(r'^favicon\.ico$', RedirectView.as_view(
        url=('/static/img/favicon_debug.ico' if settings.DEBUG else '/static/img/favicon.ico'))),

    url(r'^/?$', 'quast_app.views.index'),

    url(r'^manual/?$', 'quast_app.views.manual'),
    url(r'^manual.html$', 'quast_app.views.manual'),
    url(r'^manual_1\.3/?$', 'quast_app.views.manual'),
    url(r'^manual_1\.3\.html$', 'quast_app.views.manual'),
    url(r'^LICENSE$', 'quast_app.views.license'),
    url(r'^quast_ref\.bib$', 'quast_app.views.bib'),
    url(r'^benchmarking/?$', 'quast_app.views.benchmarking'),
    url(r'^example/?$', 'quast_app.views.example'),
    url(r'^ecoli/?$', 'quast_app.views.idba'),

    url(r'^e.coli-single-cell/(?P<download_fname>.+)?/?$', 'quast_app.example_reports_views.e_coli_sc'),
    url(r'^e.coli-isolate/(?P<download_fname>.+)?/?$', 'quast_app.example_reports_views.e_coli_mc'),

    url(r'^paper/$', 'quast_app.example_reports_views.paper'),
    url(r'^paper/e.coli/(?P<download_fname>.+)?/?$', 'quast_app.example_reports_views.e_coli'),
    url(r'^paper/b.impatiens/(?P<download_fname>.+)?/?$', 'quast_app.example_reports_views.b_impatiens'),
    url(r'^paper/h.sapiens_chr14/(?P<download_fname>.+)?/?$', 'quast_app.example_reports_views.h_sapiens'),

    url(r'^paper/h.sapiens_chr14/download/?$',
        RedirectView.as_view(url='/static/data_sets/h.sapiens_chr14/h_sapiens_chr14_quast_report.zip'),
        name='h_sapiens_quast_report'),

    url(r'^contigs-ajax-upload$', views.contigs_uploader.upload, name='contigs_ajax_upload'),
    url(r'^contigs-ajax-remove$', views.contigs_uploader.remove, name='contigs_ajax_remove'),
    url(r'^contigs-ajax-initialize-uploads$', views.contigs_uploader.initialize_uploads, name='contigs_ajax_initialize_uploads'),
    url(r'^contigs-ajax-remove-all$', views.contigs_uploader.remove_all, name='contigs_ajax_remove_all'),
    url(r'^ajax-delete-session$', views.delete_session, name='ajax_delete_session'),

    url(r'^reports/?$', quast_app.views.reports),
    url(r'^report/?$', quast_app.views.reports),

    url(r'^reports/download/(?P<link>.+)/?$', quast_app.views.download_report),
    url(r'^download-report/(?P<link>.+)$', quast_app.views.download_report),
    url(r'^report/(?P<link>.+)/?$', quast_app.views.report),
    url(r'^reports/(?P<link>.+)/?$', quast_app.views.report),

    url(r'^data-sets/(?P<data_set_id>.+)_(?P<what>.+)(?P<file_ext>\..+)$',
        views.download_data_set, name='download_data_set'),
    url(r'^data-sets/(?P<data_set_id>.+)(?P<file_ext>\..+)$',
        views.download_data_set, {'what': 'reference'}, name='download_data_set'),

    url(r'^reorder-report-columns$', quast_app.views.reorder_report_columns_ajax),

    url(r'^500', TemplateView.as_view(template_name='500.html')),
    url(r'^404', TemplateView.as_view(template_name='404.html')),

    url(r'^ask_password', quast_app.login_views.ask_password, name='ask_password_link'),
    url(r'^login', 'quast_app.login_views.login', name='login_link'),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)

for ver in ('2.5', '3.0'):
    urlpatterns += (
        url(r'^spades.' + ver + '-on-gage.b-data-sets/$',
            'quast_app.example_reports_views.spades_on_gage_b_data_sets',
            {'spades_ver': ver}),
    )

    for d_set_slug in ['b.cereus', 'm.abscessus', 'r.sphaeroides', 'v.cholerae']:
        urlpatterns += (
            url(r'^spades.' + ver + '-on-gage.b-data-sets/' + d_set_slug + '/(?P<download_fname>.+)?/?$',
                'quast_app.example_reports_views.spades_on_gage_b_data_sets__' + d_set_slug.replace('.', '_'),
                {'is_scaf': False, 'spades_ver': ver}),

            url(r'^spades.' + ver + '-on-gage.b-data-sets/' + d_set_slug + '-scaffolds/(?P<download_fname>.+)?/?$',
                'quast_app.example_reports_views.spades_on_gage_b_data_sets__' + d_set_slug.replace('.', '_'),
                {'is_scaf': True, 'spades_ver': ver}),
        )

urlpatterns += staticfiles_urlpatterns()

#import object_tools
#object_tools.autodiscover()
#urlpatterns += patterns('',
#    (r'^object-tools/', include(object_tools.tools.urls)),
#)
