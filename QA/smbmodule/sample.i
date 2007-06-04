%typemap(python, memberin) int [ANY]{
int i;
for(i=0;i<$dim0;i++)
   $target[i]=$source[i];
}

%typemap(python, in) int arr[ANY]{
 if (PyList_Check($source)) {
    int size = PyList_Size($source);
    int i = 0;
    static int arr[$dim0];
    if(size!=$dim0){
       PyErr_SetString(PyExc_TypeError,"List must have $dim0 elements");
       return NULL;
    }  
    $target=arr;
    for(i=0;i<$dim0;i++){
       PyObject *o = PyList_GetItem($source,i);
       if (PyInt_Check(o)){
	  $target[i] = (int)PyInt_AsLong(o);   
       }else{
	  PyErr_SetString(PyExc_TypeError,"List must contain integers");
	  return NULL;
       }
    }
 }
}

%inline %{
int *p_int12(int arr[12]){
return arr;
}
%}

%typemap(python, out) int* p_intout12{
	int len,i;
	len = 12;
	$target = PyList_New(len);
	for (i = 0; i < len; i++) {
	 PyList_SetItem($target,i,PyInt_FromLong((long)$source[i]));
	}
}

%inline %{
int *p_intout12(int *x){
return x;
}
%}

%inline %{
typedef struct
     {
     unsigned int Offset;
     int Range;
     int Pattern[12];
     } TriggerStructure;
%}
%pragma(python) include="mbin_ary_aux.py"



