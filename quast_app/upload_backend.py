from io import BufferedWriter, FileIO
from django.http import HttpResponseBadRequest
import os
import random
from ajaxuploader.backends.base import AbstractUploadBackend
from quast_app.models import ContigsFile, UserSession
from quast_website import settings


class MyBaseUploadBackend(AbstractUploadBackend):
    def __init__(self, dirname, **kwargs):
        super(MyBaseUploadBackend, self).__init__(**kwargs)
        self.user_session = None

    def setup(self, filename):
        dirpath = os.path.join(settings.input_root_dirpath, self.user_session.input_dirname)
        try:
            os.makedirs(dirpath)
        except:
            pass

        fpath = os.path.join(dirpath, filename)
        self._path = fpath
        self._dest = BufferedWriter(FileIO(self._path, 'w'))

    def upload_chunk(self, chunk):
        self._dest.write(chunk)

    def upload_complete(self, request, filename):
        self._dest.close()

        file_index = "%x" % random.getrandbits(128)
        c_fn = ContigsFile(fname=filename, user_session=self.user_session, file_index=file_index)
        c_fn.save()
        return {'file_index': file_index }

    def update_filename(self, request, filename):
        return filename

    def remove(self, request):
        file_index = request.GET['file_index']
        try:
            contigs_file = ContigsFile.objects.get(file_index=file_index)
        except ContigsFile.DoesNotExist:
            return HttpResponseBadRequest('No file with such index')

        if contigs_file.user_session != self.user_session:
            return HttpResponseBadRequest('This file does not belong to this session')

        contigs_fpath = os.path.join(settings.input_root_dirpath, self.user_session.input_dirname, contigs_file.fname)
        if os.path.isfile(contigs_fpath):
            os.remove(contigs_fpath)
        contigs_file.delete()
        return True

    def get_uploads(self, request):
        contigs_files = ContigsFile.objects.filter(user_session=self.user_session)
        return [{"fileName": c_f.fname, "file_index": c_f.file_index} for c_f in contigs_files]



class ContigsUploadBackend(MyBaseUploadBackend):
    def __init__(self, **kwargs):
        super(ContigsUploadBackend, self).__init__('contigs', **kwargs)


class ReferenceUploadBackend(MyBaseUploadBackend):
    def __init__(self, **kwargs):
        super(ReferenceUploadBackend, self).__init__('reference', **kwargs)


class GenesUploadBackend(MyBaseUploadBackend):
    def __init__(self, **kwargs):
        super(GenesUploadBackend, self).__init__('genes', **kwargs)


class OperonsUploadBackend(MyBaseUploadBackend):
    def __init__(self, **kwargs):
        super(OperonsUploadBackend, self).__init__('operons', **kwargs)










