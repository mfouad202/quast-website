import os
from django.conf import settings
from django.http import HttpResponse, Http404
from django.core.servers.basehttp import FileWrapper
from views_report import get_report_response_dict
from django.shortcuts import render_to_response
from django.utils.encoding import smart_str
import mimetypes


download_text = '' +\
    'Text, TSV and Latex versions<br>' +\
    'of the table, plots in PNG.<br>' +\
    '<div class="small_line_indent"></div>'


def paper(request):
    return render_to_response('paper/index.html')


def e_coli(request, download_fname):
    return common_view('paper/', 'E. coli', 'e.coli', download_fname)


def h_sapiens(request, download_fname):
    return common_view('paper/', 'H. sapiens chr. 14', 'h.sapiens_chr14', download_fname)


def b_impatiens(request, download_fname):
    return common_view('paper/', 'B. impatiens', 'b.impatiens', download_fname)


def e_coli_sc(request, download_fname):
    return common_view('', 'E. coli, single cell', 'e.coli-single-cell', download_fname)


def e_coli_mc(request, download_fname):
    return common_view('', 'E. coli, isolate', 'e.coli-isolate', download_fname)


__spades_2_5_on_gage_b__header_template = '%s MiSeq SPAdes&nbsp;2.5 assemblies'
__spades_2_5_on_gage_b__title_template = __spades_2_5_on_gage_b__header_template


def __spades_2_5_on_gage_b_data_sets__common(download_fname, name, is_scaf=False):
    slug = name.replace(' ', '').lower()

    if is_scaf:
        slug += '-scf'

    return common_view(dir_name='spades.2.5-on-gage.b-data-sets/',
                       header=__spades_2_5_on_gage_b__header_template % name.replace(' ', '&nbsp;') + ' (scaffolds)',
                       slug_name=slug, download_fname=download_fname,
                       html_template_name='common_report', data_set_name=name,
                       title=__spades_2_5_on_gage_b__title_template % name + (' (scaffolds)' if is_scaf else '')
                       )


def spades_2_5_on_gage_b_data_sets(request):
    return render_to_response('spades.2.5-on-gage.b-data-sets/index.html')


def spades_2_5_on_gage_b_data_sets__b_cereus(request, download_fname, is_scaf=False):
    return __spades_2_5_on_gage_b_data_sets__common(download_fname, 'B. cereus', is_scaf)


def spades_2_5_on_gage_b_data_sets__m_abscessus(request, download_fname, is_scaf=False):
    return __spades_2_5_on_gage_b_data_sets__common(download_fname, 'M. abscessus', is_scaf)


def spades_2_5_on_gage_b_data_sets__r_sphaeroides(request, download_fname, is_scaf=False):
    return __spades_2_5_on_gage_b_data_sets__common(download_fname, 'R. sphaeroides', is_scaf)


def spades_2_5_on_gage_b_data_sets__v_cholerae(request, download_fname, is_scaf=False):
    return __spades_2_5_on_gage_b_data_sets__common(download_fname, 'V. cholerae', is_scaf)


# def spades_2_5_on_gage_b_data_sets__b_cereus_scf(request, download_fname):
#     return common_view(dir_name='spades.2.5-on-gage.b-data-sets/',
#                        header=spades_2_5_on_gage_b__header_template % 'B.&nbsp;cereus scaffolds',
#                        slug_name='b.cereus', download_fname=download_fname,
#                        html_template_name='common_report.html',
#                        data_set_name='B. cereus',
#                        title=spades_2_5_on_gage_b__title_template % 'B. cereus scaffolds')


def common_view(dir_name, header, slug_name, download_fname, html_template_name=None, data_set_name=None, title=None):
    if not html_template_name:
        html_template_name = slug_name

    if download_fname:
        download_fpath = os.path.join(settings.FILES_DOWNLOADS_DIRPATH, download_fname)

        if os.path.exists(download_fpath):
#            if download_fname[-4:] == '.zip':
#                mimetype = 'application/zip'
#            else:
#            mimetype = 'application/force-download'

#            f = FileWrapper(fpath)
#            response = HttpResponse(mimetype=mimetype)
#            response['Content-Disposition'] = 'attachment; filename=%s' % download_fname
#            response['X-Sendfile'] = download_fpath
#            response['Content-Length'] = 100
#            return response

            wrapper = FileWrapper(open(download_fpath, 'r'))
            content_type = mimetypes.guess_type(download_fpath)[0]

            response = HttpResponse(wrapper, content_type=content_type)
            response['Content-Length'] = os.path.getsize(download_fpath)
            response['Content-Disposition'] = 'attachment; filename=' + smart_str(download_fname)

            return response

        else:
            raise Http404('File %s does not exist' % download_fname)

    else:
        response_dict = settings.TEMPLATE_ARGS_BY_DEFAULT

        report_dict = get_report_response_dict(
            os.path.join(settings.FILES_DIRPATH, dir_name, slug_name),
            caption=header,
        )
        response_dict.update(report_dict)

        response_dict['download'] = True
        response_dict['downloadLink'] = slug_name + '_quast_report.zip'
        response_dict['downloadText'] = download_text

        if data_set_name:
            response_dict['dataSetName'] = data_set_name

        if title:
            response_dict['title'] = title

        return render_to_response(dir_name + html_template_name + '.html', response_dict)
