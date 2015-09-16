def _pickle_method(method):
	func_name = method.im_func.__name__
	imobject = method.im_self
	imclass = method.im_class
	return _unpickle_method, (func_name, imobject, imclass)

def _unpickle_method(func_name, imobject, imclass):
	try:
		func = imclass.__dict__[func_name]
	except KeyError:
		pass
	return func.__get__(imobject, imclass)

import copy_reg
import types
copy_reg.pickle(types.MethodType, _pickle_method, _unpickle_method)