
# parsetab.py
# This file is automatically generated. Do not edit.
_tabversion = '3.2'

_lr_method = 'LALR'

_lr_signature = 'Y\x80_ZO+@a\xb2\xdf\x04\x9b\xc4\x18\xa0A'
    
_lr_action_items = {'END':([3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,],[-1,10,15,17,19,21,-2,-8,-18,-14,22,-15,-9,27,-7,28,-10,29,-11,-4,-12,-13,-16,-17,-5,-3,-6,]),'START2':([1,],[4,]),'START3':([1,],[5,]),'START1':([1,],[6,]),'START4':([1,],[7,]),'START5':([1,],[8,]),'ESCAPED':([11,14,24,25,26,],[-18,25,25,-16,-17,]),'TAG':([0,3,4,5,6,7,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,],[1,-1,1,1,1,1,-2,-8,-18,-14,1,-15,-9,1,-7,1,-10,1,-11,-4,-12,-13,-16,-17,-5,-3,-6,]),'CDATA':([3,4,5,6,7,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,],[-1,11,11,11,11,-2,-8,-18,-14,11,26,-9,11,-7,11,-10,11,-11,-4,-12,26,-16,-17,-5,-3,-6,]),'$end':([2,3,9,10,15,17,19,21,22,27,28,29,],[0,-1,-2,-8,-9,-7,-10,-11,-4,-5,-3,-6,]),}

_lr_action = { }
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = { }
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'body':([1,],[3,]),'empty_body':([1,],[9,]),'content':([4,5,6,7,],[13,16,18,20,]),'cdata':([4,5,6,7,13,16,18,20,],[14,14,14,14,24,24,24,24,]),'element':([0,4,5,6,7,13,16,18,20,],[2,12,12,12,12,23,23,23,23,]),}

_lr_goto = { }
for _k, _v in _lr_goto_items.items():
   for _x,_y in zip(_v[0],_v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = { }
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> element","S'",1,None,None,None),
  ('element -> TAG body','element',2,'p_element','./xnest.py',239),
  ('element -> TAG empty_body','element',2,'p_element','./xnest.py',240),
  ('body -> START1 content END','body',3,'p_body','./xnest.py',244),
  ('body -> START2 content END','body',3,'p_body','./xnest.py',245),
  ('body -> START3 content END','body',3,'p_body','./xnest.py',246),
  ('body -> START4 content END','body',3,'p_body','./xnest.py',247),
  ('empty_body -> START1 END','empty_body',2,'p_empty_body','./xnest.py',251),
  ('empty_body -> START2 END','empty_body',2,'p_empty_body','./xnest.py',252),
  ('empty_body -> START3 END','empty_body',2,'p_empty_body','./xnest.py',253),
  ('empty_body -> START4 END','empty_body',2,'p_empty_body','./xnest.py',254),
  ('empty_body -> START5 END','empty_body',2,'p_empty_body','./xnest.py',255),
  ('content -> content element','content',2,'p_content','./xnest.py',259),
  ('content -> content cdata','content',2,'p_content','./xnest.py',260),
  ('content -> element','content',1,'p_content0','./xnest.py',264),
  ('content -> cdata','content',1,'p_content0','./xnest.py',265),
  ('cdata -> cdata ESCAPED','cdata',2,'p_cdata','./xnest.py',269),
  ('cdata -> cdata CDATA','cdata',2,'p_cdata','./xnest.py',270),
  ('cdata -> CDATA','cdata',1,'p_cdata0','./xnest.py',274),
]
