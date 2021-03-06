#/usr/bin/python
# -*- coding: utf-8 -*-
#
from pycparser import parse_file, c_parser
import hashlib
from pprint import pprint
from pycparser.c_ast import *
from copy import copy
import time

ans1 = dict()
ans2 = dict()
class func_count:
	"""Функтор-счетчик"""
	count = 0
	def __call__(self):
		self.count += 1
		return self.count

arr_arr = {}
varr_arr = {}
fc_var = func_count()
fc_func = func_count()
fc_type = func_count()

import time
def timer(f):
	def tmp(*args, **kwargs):
		t = time.time()
		res = f(*args, **kwargs)
		pprint("Время выполнения функции: %f" % (time.time()-t))
		return res

	return tmp

def strange_check_1(a, b):
	if not(a is None or b is None):
		return comp_subtrees(a, b)
	return a is None and b is None

#@timer
def comp_subtrees(self, other, hash1 = None, hash2 = None, h = [{},{}]):
	if hash1 is not None:
		h[0].clear()
		h[0].update(hash1)
	if hash2 is not None:
		h[1].clear()
		h[1].update(hash2)

#	pprint (type(other))
	if type(other) == type(self):
		if type(other) in (ID, Decl) and (self.id != None) and (other.id != None):
			if (self.id not in h[0]) and (other.id not in h[1]) and (varr_arr[self.id]==varr_arr[other.id]):
				h[0][self.id] = [other.id, 1, other.coord.file, other.coord.line]
				h[1][other.id] = [self.id, 1, self.coord.file, self.coord.line]
			elif (self.id in h[0]) and (other.id in h[1]) and (h[0][self.id][0]==other.id):
				h[0][self.id][1] += 1
				h[1][other.id][1] += 1
			else:
				return False
		#TODO Temp for typedef. Понять, как улучшить код.
		elif type(other) == FuncDef:

			temp_list1 = [self.body]
			temp_list2 = [other.body]
			cm = lambda x: x is not None and x.type is not None
			if filter(cm, [other.decl, self.decl]):
				temp_list1.append([self.decl.type.args, self.decl.type.type])
				temp_list2.append([other.decl.type.args, other.decl.type.type])
			elif len(filter(cm, [other.decl, self.decl])) == 1:
				return False

			return reduce(lambda x,y: x and y, [True].extend(map(strange_check_1, temp_list1, temp_list2)))

		elif type(other) == FuncCall:
			pass
		#End of TODO

		else:
			return reduce(
				lambda x,y: x and y,
				[True].extend(map(strange_check_1, self.children(), other.children()))
			)
	return False

def get_number_of_children(node):
	if node == None:
		return 0
	child = node.children()
	return sum([get_number_of_children(i) for i in child]) + 1


def hashes_func(obj, h_array):
	substr = ""
	stri = ""#obj.assist()
	many = obj.children()
	for subobj in many:
		stri += hashes_func(subobj, h_array)
	if stri is not "":
		if hash(stri) in h_array:
			h_array[hash(stri)] += [obj]
		else:
			h_array[hash(stri)] = [obj]
	return stri

def expand_decl(decl, type_arr):
	typ = type(decl)

	if typ == TypeDecl:
		return expand_decl(decl.type, type_arr)
	elif typ == IdentifierType:
#		return decl.names
		if decl.names[0] in type_arr:		#???
			return type_arr[decl.names[0]][1]#???
		else:
			return decl.names
	elif typ == ID:
		return decl.name
	elif typ in [Struct, Union]:
		decls = [expand_decl(d, type_arr) for d in decl.decls or []]
		return [typ.__name__, decl.name, decls]
	elif typ == Enum:
		if decl.values != None:
			return ['Enum', len(decl.values.enumerators)]
	else:
		nested = expand_decl(decl.type, type_arr)

		if typ == Decl:
			if decl.quals:
				return [decl.quals, nested]
			else:
				return nested
		elif typ == Typename:
			if decl.quals:
				return [decl.quals, nested]
			else:
				return nested
		elif typ == ArrayDecl:
			dimval = decl.dim.value if decl.dim else ''
			return [dimval, nested]
		elif typ == PtrDecl:
			return ['*', nested]
		elif typ == Typedef:
			return [decl.name, nested]
		elif typ == FuncDecl:
			if decl.args:
				params = [expand_decl(param, type_arr) for param in decl.args.params]
			else:
				params = []
			return [params, nested]

def expand_init(init):
	if not init is None:
		typ = type(init)
		if typ == NamedInitializer:
			des = [expand_init(dp) for dp in init.name]
			return (des, expand_init(init.expr))
		elif typ == ExprList:
			return [expand_init(expr) for expr in init.exprs]
		elif typ == Constant:
			return ['Constant', init.type, init.value]

		elif typ == ID:
			return ['ID', init.name]
	else:
		return
#@timer
def UncryptDecl(node, var_arr = None, type_arr = None, type_undone_arr = None, func_arr = None):
	if var_arr == None:
		var_arr = {}
	if type_arr == None:
		type_arr = {}
	if type_undone_arr == None:
		type_undone_arr = {}
	if func_arr == None:
		func_arr = {}

	types = []
	typ = type(node)
	if typ == ID:
		if not node.name in var_arr.keys():
			node.id = 'smth'
		else:
			node.id = copy(var_arr[node.name][0])

	#TODO возможны зацикливания из-за неверных и рассистких высказываний. fuck lol
	elif typ == FuncCall:
		if node.name.name in func_arr.keys():
			node.name.id = func_arr[node.name.name][0]
		else:
			node.name.id = 'StandartFunction'
		if not node.args is None:
			for i in node.args.exprs:
				UncryptDecl(i, copy(var_arr), copy(type_arr), copy(type_undone_arr), copy(func_arr))
	else:
		if typ == Decl:
			if node.name != None:
				node.id=fc_var()
				var_arr[node.name]=[node.id, expand_decl(node, type_arr)]
				if node.name not in arr_arr.keys():#debug
					arr_arr[node.name] = [node.id, expand_decl(node, type_arr)]#debug
				else:#debug 
					arr_arr[node.name] += [node.id, expand_decl(node, type_arr)]#debug
				if node.id not in varr_arr.keys():
					varr_arr[node.id] = [expand_decl(node, type_arr)]
				else:
					varr_arr[node.id] += [expand_decl(node, type_arr)]
			if node.init != None:
				UncryptDecl(node.init, var_arr, type_arr, type_undone_arr, func_arr)
			if type(node.type) in [Struct, Union, Enum] and node.type.name != None:
				type_undone_arr[node.type.name]=[fc_type(), expand_decl(node, type_arr)[2]]
				pprint(type_undone_arr)

		elif typ == Typedef:
			if type(node.type) in [Struct, Union, Enum] and node.type.decls == None:
				type_arr[node.name] = type_undone_arr[node.type.name]
			else:
				type_arr[node.name] = [fc_type, expand_decl(node.type, type_arr)]

		elif typ == FuncDef:
			arr = {}
			if node.decl.type.args != None:
				for i in node.decl.type.args.params:
					UncryptDecl(i, var_arr, type_arr, type_undone_arr, func_arr)

			if not node.decl.name in func_arr.keys():
				func_arr[node.decl.name]=[fc_func() ,expand_init(node.decl.type.type), arr]
				node.decl.id = func_arr[node.decl.name][0]
			else:
				raise(Exception("{0} repeated twice".format(node.decl.name)))
			var_arr_updated = copy(var_arr)
			var_arr_updated.update(arr)
			UncryptDecl(node.body, var_arr_updated, copy(type_arr), copy(type_undone_arr), copy(func_arr))

		else:
			for i in node.children():
				if type(i) in [Decl, FuncDef, DeclList, Typedef]:
					UncryptDecl(i, var_arr, type_arr, type_undone_arr, func_arr)
				else:
					UncryptDecl(i, copy(var_arr), copy(type_arr), copy(type_undone_arr), copy(func_arr))
@timer
def parsing_file(filename, ans, debug=None):
	if debug == None:
		debug = False
	node = parse_file(filename)
	hashes_func(node, ans)
	UncryptDecl(node)
	if debug:
		node.show()
	return node

if __name__ == "__main__":
	if len(sys.argv) > 2:
		filename1  = sys.argv[1]
		filename2  = sys.argv[2]
	else:
		filename1 = 'main1.c'
		filename2 = 'main2.c'
	t1 = parsing_file(filename1, ans1)
	t2 = parsing_file(filename2, ans2)
	first = {}
	second = {}
	third = []
	fourth = []

	pprint(comp_subtrees(t1,t2,{},{}))
	for i in ans1:
		if i in ans2:
			for j in ans1[i]:
				for k in ans2[i]:
					comp_subtrees(j, k, first, second)
					if first != {}:
						third.append([copy(first), copy(second), j, k])
						first = {}
						second = {}
			if third != []:
				fourth.append(copy(third))
				third = []
	
	pprint(fourth)
#	pprint(arr_arr)
#	pprint(varr_arr)
#	for i in t1.children():
#		pass
#	UncryptDecl(t1)
#	t1.show()
