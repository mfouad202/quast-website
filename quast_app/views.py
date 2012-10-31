import sys
import datetime
from celery.app.task import Task
from django.core.urlresolvers import reverse
from django.forms import forms
import os
import shutil
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, render, redirect
import tasks
from upload_backend import ContigsUploadBackend, ReferenceUploadBackend, GenesUploadBackend, OperonsUploadBackend
from django.conf import settings


glossary = '{}'
with open(os.path.join(settings.GLOSSARY_PATH)) as f:
    glossary = f.read()


def add_template_args_by_defualt(new_args):
    together = dict(new_args)
    together['glossary'] = glossary
    together['google-analytics'] = settings.GOOGLE_ANALYTICS
    return together


template_args_by_default = {
    'glossary': glossary,
    'google-analytics': settings.GOOGLE_ANALYTICS,
}


def manual(request):
    with open(settings.MANUAL_FPATH) as f:
        return HttpResponse(f.read())


def license(request):
    with open(settings.LICENSE_FPATH) as f:
        return HttpResponse(f.read(), content_type='text/plain')


def example(request):
    example_dirpath = os.path.join(settings.EXAMPLE_DIRPATH)
    response_dict = get_report_response_dict(example_dirpath, 'E.coli')
    return render_to_response('example-report.html', response_dict)


def benchmarking(request):
    return render_to_response('benchmarking.html', template_args_by_default)


def ecoli(request):
    return render_to_response('ecoli.html',
          get_report_response_dict(os.path.join(settings.ECOLI_DIRPATH), 'E.coli')
    )


#def report_scripts(request, script_name):
#    with open(os.path.join(settings.REPORT_SCRIPTS_DIRPATH, script_name)) as f:
#        return HttpResponse(f.read(), content_type='application/javascript')


from django.middleware.csrf import get_token
from django.template import RequestContext
from ajaxuploader.views import AjaxFileUploader
from models import UserSession, Dataset, QuastSession, ContigsFile, QuastSession_ContigsFile
from forms import DatasetForm

#if not request.session.exists(request.session.session_key):
#request.session.create()

if not settings.QUAST_DIRPATH in sys.path:
    sys.path.insert(1, settings.QUAST_DIRPATH)
from libs import qconfig


contigs_uploader = AjaxFileUploader(backend=ContigsUploadBackend)
#reference_uploader = AjaxFileUploader(backend=ReferenceUploadBackend)
#genes_uploader = AjaxFileUploader(backend=GenesUploadBackend)
#operons_uploader = AjaxFileUploader(backend=OperonsUploadBackend)


state_map = {
    'PENDING': 'PENDING',
    'STARTED': 'PENDING',
    'FAILURE': 'FAILURE',
    'SUCCESS': 'SUCCESS',
}


def index(request):
    if not request.session.exists(request.session.session_key):
        request.session.create()

    user_session_key = request.session.session_key
    try:
        user_session = UserSession.objects.get(session_key=user_session_key)
    except UserSession.DoesNotExist:
        user_session = create_user_session(user_session_key)

    response_dict = template_args_by_default
    response_dict['session_key'] = user_session_key


    # EVALUATE
    contigs_fnames = [c_f.fname for c_f in user_session.contigsfile_set.all()]

    if request.method == 'POST':
        data_set_form = DatasetForm(request.POST)
        data_set_form.set_user_session(user_session)
        #        dataset_form.fields['name_selected'].choices = dataset_choices
        if data_set_form.is_valid():
            from datetime import datetime
            now_datetime = datetime.now()
            now_str = now_datetime.strftime('%d_%b_%Y_%H:%M:%S.%f')

            min_contig = data_set_form.cleaned_data['min_contig']
            request.session['min_contig'] = min_contig
            data_set = get_dataset(request, data_set_form, now_str)
            quast_session = start_quast_session(user_session, data_set, min_contig, now_datetime)
#            return HttpResponseRedirect(reverse('quast_app.views.index', kwargs={'after_evaluation': True}))
            request.session['after_evaluation'] = True
            return redirect(index)

        else:
            min_contig = request.session.get('min_contig') or qconfig.min_contig
            request.session['min_contig'] = min_contig
            data_set_form.set_min_contig(min_contig)

    else:
        data_set_form = DatasetForm()
        min_contig = request.session.get('min_contig') or qconfig.min_contig
        data_set_form.set_min_contig(min_contig)

    response_dict = dict(response_dict.items() + {
        'csrf_token': get_token(request),
        'contigs_fnames': contigs_fnames,
        'dataset_form': data_set_form,
    }.items())


    # REPORTS
    reports_dict = get_reports_response_dict(
        user_session,
        after_evaluation=request.session.get('after_evaluation', False),
        limit=13)
    response_dict = dict(response_dict.items() + reports_dict.items())
    request.session['after_evaluation'] = False


    # EXAMPLE
    example_dirpath = os.path.join(settings.EXAMPLE_DIRPATH)
    example_dict = get_report_response_dict(example_dirpath, 'E.coli')
    response_dict = dict(response_dict.items() + example_dict.items())

    return render_to_response(
        'index.html',
        response_dict,
        context_instance = RequestContext(request)
    )


def get_evaluate_response_dict(request, user_session, url):
    contigs_fnames = [c_f.fname for c_f in user_session.contigsfile_set.all()]

    if request.method == 'POST':
        data_set_form = DatasetForm(request.POST)
        data_set_form.set_user_session(user_session)
        #        dataset_form.fields['name_selected'].choices = dataset_choices
        if data_set_form.is_valid():
            from datetime import datetime
            now_datetime = datetime.now()
            now_str = now_datetime.strftime('%d_%b_%Y_%H:%M:%S.%f')

            min_contig = data_set_form.cleaned_data['min_contig']
            request.session['min_contig'] = min_contig
            data_set = get_dataset(request, data_set_form, now_str)
            quast_session = start_quast_session(user_session, data_set, min_contig, now_datetime)

            return redirect(url, after_evaluation=True)

        else:
            min_contig = request.session.get('min_contig') or qconfig.min_contig
            request.session['min_contig'] = min_contig
            data_set_form.set_min_contig(min_contig)

        #            return render_to_response('reports.html', {
        #                'glossary': glossary,
        #                'csrf_token': get_token(request),
        #                'session_key': user_session_key,
        #                'contigs_fnames': contigs_fnames,
        #                'dataset_form': dataset_form,
        #                'report_id': quast_session.report_id,
        #                }, context_instance = RequestContext(request))
    else:
        data_set_form = DatasetForm()
        min_contig = request.session.get('min_contig') or qconfig.min_contig
        data_set_form.set_min_contig(min_contig)

    #        dataset_form.fields['name_selected'].choices = dataset_choices

    response_dict = template_args_by_default
    response_dict = dict(response_dict.items() + {
        'csrf_token': get_token(request),
        'contigs_fnames': contigs_fnames,
        'dataset_form': data_set_form,
    }.items())

    return response_dict



def evaluate(request):
    if not request.session.exists(request.session.session_key):
        request.session.create()

    user_session_key = request.session.session_key
    try:
        user_session = UserSession.objects.get(session_key=user_session_key)
    except UserSession.DoesNotExist:
        user_session = create_user_session(user_session_key)

    response_dict = get_evaluate_response_dict(request, user_session, '/evaluate/')
    return render_to_response('evaluate.html', response_dict, context_instance = RequestContext(request))



def get_reports_response_dict(user_session, after_evaluation=False, limit=None):
    quast_sessions_dict = []

    quast_sessions = user_session.quastsession_set.order_by('-date')
    if limit:
        quast_sessions = quast_sessions[:limit+1]

    show_more_link = False

    if quast_sessions.exists():
#        quast_sessions.sort(cmp=lambda qs1, qs2: 1 if qs1.date < qs2.date else -1)

#        if after_evaluation:
#            last = quast_sessions[0]
#            result = tasks.start_quast.AsyncResult(last.task_id)
#            if result and result.state == 'SUCCESS':
#                return redirect('/report/', report_id=last.report_id)

        for i, qs in enumerate(quast_sessions):
            if i == limit:
                show_more_link = True
            else:
                result = tasks.start_quast.AsyncResult(qs.task_id)
                state = result.state
                state_repr = 'FAILURE'
                if result and state in state_map:
                    state_repr = state_map[state]

                quast_session_info = {
                    'date': qs.date, #. strftime('%d %b %Y %H:%M:%S'),
                    'report_link': '/report/' + qs.report_id,
                    'with_dataset': True if qs.dataset else False,
                    'dataset_name': qs.dataset.name if qs.dataset and qs.dataset.remember else '',
                    'state': state_repr,
                }
                quast_sessions_dict.append(quast_session_info)

    return {
        'quast_sessions': quast_sessions_dict,
        'show_more_link': show_more_link,
        'highlight_last': after_evaluation,
#        'highlight_last': True,
        'latest_report_link': quast_sessions_dict[0]['report_link'] if after_evaluation else None
    }


def reports(request, after_evaluation=False):
    if not request.session.exists(request.session.session_key):
        request.session.create()

    user_session_key = request.session.session_key
    try:
        user_session = UserSession.objects.get(session_key=user_session_key)
    except UserSession.DoesNotExist:
        user_session = create_user_session(user_session_key)

    response_dict = get_reports_response_dict(user_session, after_evaluation)
    return render_to_response('reports.html', response_dict)



def create_user_session(user_session_key):
    input_dirpath = os.path.join(settings.INPUT_ROOT_DIRPATH, user_session_key)
    if os.path.isdir(input_dirpath):
        shutil.rmtree(input_dirpath)
    os.makedirs(input_dirpath)

    user_session = UserSession(
        session_key = user_session_key,
        input_dirname = user_session_key,
        )
    user_session.save()
    return user_session


def get_dataset(request, dataset_form, now_str):
    if dataset_form.cleaned_data['is_created'] == True:
        name = dataset_form.data['name_created']

        def init_folders(dataset):
            dataset_dirpath = os.path.join(settings.DATA_SETS_ROOT_DIRPATH, dataset.dirname) #, posted_file.name)
            os.makedirs(dataset_dirpath)

            for kind in ['reference', 'genes', 'operons']:
                posted_file = request.FILES.get(kind)
                if posted_file:
                    with open(os.path.join(dataset_dirpath, posted_file.name), 'wb+') as f:
                        for chunk in posted_file.chunks():
                            f.write(chunk)
                    setattr(dataset, kind + '_fname', posted_file.name)

        if name == '':
            dataset = Dataset(name=now_str, remember=False)
            dataset.save()
            init_folders(dataset)
            dataset.save()

        elif not Dataset.objects.filter(name=name).exists():
            dataset = Dataset(name=name, remember=True)
            dataset.save()
            init_folders(dataset)
            dataset.save()

        else:
            dataset = Dataset.objects.get(name=name)
            #TODO: invalidate

    else:
        name = dataset_form.data['name_selected']
        if name == 'no data set':
            dataset = None
        else:
            try:
                dataset = Dataset.objects.get(name=name)
            except Dataset.DoesNotExist:
                return HttpResponseBadRequest('Data set does not exist')

    return dataset


def report(request, report_id):
    if not request.session.exists(request.session.session_key):
        request.session.create()

    user_session_key = request.session.session_key
    try:
        user_session = UserSession.objects.get(session_key=user_session_key)
    except UserSession.DoesNotExist:
        user_session = create_user_session(user_session_key)


    if QuastSession.objects.filter(report_id=report_id).exists():
        if request.method == 'GET':
            quast_session = QuastSession.objects.get(report_id=report_id)
            result = tasks.start_quast.AsyncResult(quast_session.task_id)
            state = result.state

            response_dict = template_args_by_default

            if state == 'SUCCESS':
                header = 'Quality assessment'
                if quast_session.dataset and quast_session.dataset.remember:
                    header = quast_session.dataset.name

                response_dict = dict(response_dict.items() + get_report_response_dict(
                    os.path.join(settings.RESULTS_ROOT_DIRPATH, quast_session.get_results_reldirpath()),
                    header
                ).items())

                return render_to_response('assess-report.html', response_dict)

            else:
                state_repr = 'FAILURE'
                if result and state in state_map:
                    state_repr = state_map[state]

                response_dict = dict(response_dict.items() + {
                    'csrf_token': get_token(request),
                    'session_key' : request.session.session_key,
                    'state': state_repr,
                    'report_id': report_id,
                }.items())

                return render_to_response('waiting-report.html', response_dict, context_instance = RequestContext(request))

        if request.method == 'POST':
            #check status of quast session, return result
            raise Http404()

    else:
        if request.method == 'GET':
            raise Http404()

        if request.method == 'POST':
            raise Http404()


def start_quast_session(user_session, dataset, min_contig, now_datetime):
    # Creating new Quast session object
    quast_session = QuastSession(
        user_session = user_session,
        dataset = dataset,
        date = now_datetime,
    )

    quast_session.save()

    for c_fn in user_session.contigsfile_set.all():
        QuastSession_ContigsFile.objects.create(quast_session=quast_session, contigs_file=c_fn)

    input_dirpath = os.path.join(settings.INPUT_ROOT_DIRPATH, user_session.input_dirname)

    # Preparing contigs filepaths
    print quast_session.get_results_reldirpath()
    contigs_files = quast_session.contigs_files.all()
    contigs_fpaths = [os.path.join(input_dirpath, c_f.fname) for c_f in contigs_files]

    # Preparing results directory
    result_dirpath = os.path.join(settings.RESULTS_ROOT_DIRPATH, quast_session.get_results_reldirpath())
    if os.path.isdir(result_dirpath):
        i = 2
        base_dir_path = result_dirpath
        while os.path.isdir(result_dirpath):
            result_dirpath = base_dir_path + '_' + str(i)
            i += 1
    if not os.path.isdir(result_dirpath):
        os.makedirs(result_dirpath)

    # Preparing dataset files
    reference_fpath = None
    genes_fpath = None
    operons_fpath = None
    if dataset:
        if dataset.reference_fname:
            reference_fpath = os.path.join(settings.DATA_SETS_ROOT_DIRPATH, dataset.dirname, dataset.reference_fname)

        if dataset.genes_fname:
            genes_fpath = os.path.join(settings.DATA_SETS_ROOT_DIRPATH, dataset.dirname, dataset.genes_fname)

        if dataset.operons_fname:
            operons_fpath = os.path.join(settings.DATA_SETS_ROOT_DIRPATH, dataset.dirname, dataset.operons_fname)

    # Running Quast
    result = assess_with_quast(result_dirpath, contigs_fpaths, min_contig, reference_fpath, genes_fpath, operons_fpath)
    quast_session.task_id = result.id
    quast_session.save()
    return quast_session


def assess_with_quast(res_dirpath, contigs_paths, min_contig=0, reference_path=None, genes_path=None, operons_path=None):
    if len(contigs_paths) > 0:
        if os.path.isfile(settings.QUAST_PY_FPATH):
            args = [settings.QUAST_PY_FPATH] + contigs_paths
            if reference_path:
                args.append('-R')
                args.append(reference_path)

            if genes_path:
                args.append('-G')
                args.append(genes_path)

            if operons_path:
                args.append('-O')
                args.append(operons_path)

            if min_contig:
                args.append('--min-contig')
                args.append(min_contig)

            args.append('-J')
            args.append(res_dirpath)

            # Draw no plots
            args.append('-p')

            args.append('-o')
            args.append(os.path.join(res_dirpath, 'regular_report'))

            from tasks import start_quast
            result = start_quast.delay(args)

            return result
        else:
            if not os.path.isfile(settings.QUAST_PY_FPATH):
                raise Exception('quast_py_fpath ' + settings.QUAST_PY_FPATH + ' is not a file')
    else:
        raise Exception('no files with assemblies')


def get_report_response_dict(results_dirpath, header):
    if dir is None:
        raise Exception('No results directory.')

    def get(name, is_required=False, msg=None):
        contents = ''
        try:
            f = open(os.path.join(results_dirpath, name + '.json'))
            contents = f.read()
        except IOError:
            if is_required:
                raise Exception(name + ' is not found but required.')
        return contents

    try:
        total_report = get('total_report', is_required=True)
    except Exception, e:
        total_report = get('report', is_required=True)

    contigs_lengths         = get('contigs_lengths', is_required=True)
    reference_length        = get('ref_length')
    assemblies_lengths      = get('assemblies_lengths')
    aligned_contigs_lengths = get('aligned_contigs_lengths')
    contigs                 = get('contigs')
    genes                   = get('genes')
    operons                 = get('operons')
    gc_info                 = get('gc')

    if not settings.QUAST_DIRPATH in sys.path:
        sys.path.insert(1, settings.QUAST_DIRPATH)
    from libs import reporting

    import json
    quality_dict = json.dumps(reporting.Fields.quality_dict)
    main_metrics = json.dumps(reporting.get_main_metrics())

    return {
        'totalReport' : total_report,
        'contigsLenghts' : contigs_lengths,
        'alignedContigsLengths' : aligned_contigs_lengths,
        'assembliesLengths' : assemblies_lengths,
        'referenceLength' : reference_length,
        'contigs' : contigs,
        'genes' : genes,
        'operons' : operons,
        'gcInfo' : gc_info,

        'header' : header,

        'qualities': quality_dict,
        'mainMetrics': main_metrics,
    }


#static_path = 'app/static/'
#
#def get_static_file(request, path):
#    try:
#        contents = open(static_path + path)
#    except IOError:
#        return ''
#    else:
#        return HttpResponse(contents)


#def tar_archive(request, version):
#    path = '/Users/vladsaveliev/Dropbox/bio/quast/quast_website/quast' + version + '.tar.gz'
#
#    if os.path.isfile(path):
#        response = HttpResponse(mimetype='application/x-gzip')
#        response['Content-Disposition'] = 'attachment; filename=quast' + version +'.tar.gz'
#        response['X-Sendfile'] = path
#        return response
#    else:
#        raise Http404
