import base64
import binascii
import os
import subprocess
import sys
from tempfile import NamedTemporaryFile


def create_temp_file(content: str, ext: str, encoding: str) -> NamedTemporaryFile:
    # initial processing of content, generate a bytestring respecting possible unicode escapes
    try:
        processed_content = content.encode('ascii').decode('unicode-escape').encode('ascii')
    except UnicodeError as err:
        raise RuntimeError("Could not read base64 string from file content") from err

    # base64 decode byte string
    try:
        message_bytes = base64.b64decode(processed_content)
    except binascii.Error as err:
        raise RuntimeError("Could not decode base64 decode file content") from err

    # create temporary file and encode content (needs to be deleted manually, so other processes can access it)
    try:
        if encoding == "binary":
            file = NamedTemporaryFile(mode='w+b', suffix="." + ext, delete=False)
            encoded_content = message_bytes
        else:
            # Use the same encoding for writing as for reading
            file = NamedTemporaryFile(mode='w+', suffix="." + ext, delete=False, encoding=encoding)
            encoded_content = message_bytes.decode(encoding)
    except OSError as err:
        raise RuntimeError("Could not create temporary file") from err
    except UnicodeError as err:
        destroy_temp_file(file)
        raise RuntimeError(f"Could not decode content in with {encoding} encoding") from err

    # write content to file
    try:
        file.write(encoded_content)
        file.close()
    except (RuntimeError, IOError, OSError) as err:
        destroy_temp_file(file)
        raise RuntimeError("Could not write decoded content to temporary file") from err

    return file


def destroy_temp_file(file: NamedTemporaryFile):
    os.remove(file.name)


def raise_(tp, value=None, tb=None):
    """
    A function that matches the Python 2.x ``raise`` statement. This
    allows re-raising exceptions with the cls value and traceback on
    Python 3.
    """
    if value is not None and isinstance(tp, Exception):
        raise TypeError("instance exception may not have a separate value")
    if value is not None:
        exc = tp(value)
    else:
        exc = tp
    if exc.__traceback__ is not tb:
        raise exc.with_traceback(tb)
    raise exc


class OutOfProcess(object):
    def __init__(self, cmd: str, args: list[str]):
        self.args = args
        self.cmd = cmd
        self.process = None
        self.exc_info = None
        self.str_out = ""
        self.str_err = ""

    def start(self, inp: str):
        cmd = [self.cmd] + self.args + [inp]
        # print(f"[INFO] command: {cmd}")
        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, text=True)
            self.str_out, self.str_err = self.process.communicate()
        except:
            self.exc_info = sys.exc_info()

        # execution failed
        if self.exc_info:
            raise_(*self.exc_info)

        # spawning failed
        if self.process is None:
            raise RuntimeError('Could not spawn ' + ' '.join(cmd))

        return self.process.returncode, self.str_out, self.str_err

    def kill(self):
        try:
            if self.process is not None:
                self.process.kill()
        except:
            self.exc_info = sys.exc_info()
            raise_(*self.exc_info)
