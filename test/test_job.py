from shutil import copyfile
from dataclasses import dataclass

from wstr.job import Job

@dataclass
class FileStub(object):
    filename:str

    def save(self, dest):
        copyfile(self.filename, dest)

# def test_job():
#     stub = FileStub("resource/demo.txt")
#     job = Job(0, "", "X", 3, "", stub)
#     assert job.status == Job.Status.Queued
#     assert job.n_pops == 3
#     assert job.n_loci == 0
#     assert job.n_samples == 0

#     job.execute()
#     assert job.n_loci == 62
#     assert job.n_samples == 23
#     assert job.status == Job.Status.Complete
