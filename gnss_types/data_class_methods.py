"""
    Author: Kanstantsin Yuryeu
    Mail: konstantin.yuriev83@gmail.com

    This file implements some usefull methods for gnss dataclass objects.
"""

import math
import copy
from dataclasses import dataclass, fields, is_dataclass, asdict
from collections.abc import Iterable


DEF_FLOAT_CMP_TOLR = 1e-15

@dataclass
class DataClassMethods:
    
    def items(self):
        for field in fields(self.__class__):
            yield field.name, getattr(self, field.name)

    def copy(self):
        """Shallow copy of the object"""
        ret = self.__class__()
        for key, value in self.items():
            setattr(ret,key,value)

        return ret
    
    def deepcopy(self):
        """Return deep copy of the object"""
        return copy.deepcopy(self)
    
    def len(self):
        return len(fields(self))
    
    
    @classmethod
    def __compare(cls, A, B, f_tolerance:float) -> bool:
        """ Compare 'A' versus 'B'.
            Integer and string fields shall match absolutely.
            Floats are compared with predefined relative tolerance.
            Comparison is done in 'deep' manner - goes recursively 
            through compound elements untll decomposed to primitives. 
            """

        if type(A) != type(B):
            return False
        
        if is_dataclass(A):
            A = asdict(A)
            B = asdict(B)
        
        if isinstance(A, (int, str, bool)):
            return (A == B)
        
        elif isinstance(A, float):
            if math.fabs(B > f_tolerance):
                diff = math.fabs((B-A)/B)
            else:
                diff = math.fabs(B-A)
            return (diff < f_tolerance)
                    
        elif isinstance(A, dict):

            if A.keys() != B.keys():
                return False
            
            for key in A:
                if not cls.__compare(A[key],B[key],f_tolerance):
                    return False

        elif isinstance(A, Iterable):
            
            if len(A) != len(B):
                return False

            for a, b in zip(A, B):
                if not cls.__compare(a,b,f_tolerance):
                    return False
    
        else:
            raise TypeError(f'Unexpected type {type(A)}. Comparison is impossible.')
        
        return True
       
    
    def compare(self, refs, f_tolerance:float = DEF_FLOAT_CMP_TOLR) -> bool:
        """ Compare versus 'refs' field by field.
            Integer and string fields shall match absolutely.
            Floats are compared with predefined relative tolerance.
            Compaund fields are checked recursively (deep comparison)."""

        if type(self) != type(refs):
            return False
        
        for key, value in self.items():
            try:
                ref = getattr(refs,key)
            except IndexError:
                return False
            
            if is_dataclass(value):
                eq = value.compare(ref)
            else:
                eq = self.__compare(value,ref,f_tolerance)
            
            if not eq:
                return False

        return True