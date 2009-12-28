
# parsetab.py
# This file is automatically generated. Do not edit.
_tabversion = '3.2'

_lr_method = 'LALR'

_lr_signature = '\x1e\xbd\xc7\xae\x85\t\xff\xb1\x8ftY\xed\xab\xd2@f'
    
_lr_action_items = {'END':([3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,],[-1,9,14,16,18,-2,-8,-17,-13,20,-14,-9,25,-7,26,-10,27,-4,-11,-12,-15,-16,-5,-3,-6,]),'START2':([1,],[4,]),'START3':([1,],[5,]),'START1':([1,],[6,]),'START4':([1,],[7,]),'ESCAPED':([10,13,22,23,24,],[-17,23,23,-15,-16,]),'TAG':([0,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,],[1,-1,1,1,1,1,-2,-8,-17,-13,1,-14,-9,1,-7,1,-10,1,-4,-11,-12,-15,-16,-5,-3,-6,]),'CDATA':([3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,],[-1,10,10,10,10,-2,-8,-17,-13,10,24,-9,10,-7,10,-10,10,-4,-11,24,-15,-16,-5,-3,-6,]),'$end':([2,3,8,9,14,16,18,20,25,26,27,],[0,-1,-2,-8,-9,-7,-10,-4,-5,-3,-6,]),}

_lr_action = { }
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = { }
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'body':([1,],[3,]),'empty_body':([1,],[8,]),'content':([4,5,6,7,],[12,15,17,19,]),'cdata':([4,5,6,7,12,15,17,19,],[13,13,13,13,22,22,22,22,]),'element':([0,4,5,6,7,12,15,17,19,],[2,11,11,11,11,21,21,21,21,]),}

_lr_goto = { }
for _k, _v in _lr_goto_items.items():
   for _x,_y in zip(_v[0],_v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = { }
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> element","S'",1,None,None,None),
  ('element -> TAG body','element',2,'p_element','xnest.py',211),
  ('element -> TAG empty_body','element',2,'p_element','xnest.py',212),
  ('body -> START1 content END','body',3,'p_body','xnest.py',217),
  ('body -> START2 content END','body',3,'p_body','xnest.py',218),
  ('body -> START3 content END','body',3,'p_body','xnest.py',219),
  ('body -> START4 content END','body',3,'p_body','xnest.py',220),
  ('empty_body -> START1 END','empty_body',2,'p_empty_body','xnest.py',225),
  ('empty_body -> START2 END','empty_body',2,'p_empty_body','xnest.py',226),
  ('empty_body -> START3 END','empty_body',2,'p_empty_body','xnest.py',227),
  ('empty_body -> START4 END','empty_body',2,'p_empty_body','xnest.py',228),
  ('content -> content element','content',2,'p_content','xnest.py',233),
  ('content -> content cdata','content',2,'p_content','xnest.py',234),
  ('content -> element','content',1,'p_content0','xnest.py',239),
  ('content -> cdata','content',1,'p_content0','xnest.py',240),
  ('cdata -> cdata ESCAPED','cdata',2,'p_cdata','xnest.py',245),
  ('cdata -> cdata CDATA','cdata',2,'p_cdata','xnest.py',246),
  ('cdata -> CDATA','cdata',1,'p_cdata0','xnest.py',251),
]
