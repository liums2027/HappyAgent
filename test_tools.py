import inspect

from tools import list_files
from security import check_params_error, model_from_func

files = list_files("G:\\AIWorkSpace\\HappyCoding")
for path in files:
    print(path)

error = check_params_error(list_files, '{"path": "G:/123"}')
print(error)
