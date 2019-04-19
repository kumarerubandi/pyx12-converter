import pyx12.xmlx12_simple
import libxml2
import cStringIO
import pyx12.segment
import os, os.path, sys
import logging
#from types import *

# Intrapackage imports
from pyx12 import error_handler,error_999,error_debug,error_html, errors, map_index,map_if,x12file
from pyx12.map_walker import walk_tree

NodeType = {'element_start': 1, 'element_end': 15, 'attrib': 2, 'text': 3,
    'CData': 4, 'entity_ref': 5, 'entity_decl':6, 'pi': 7, 'comment': 8,
    'doc': 9, 'dtd': 10, 'doc_frag': 11, 'notation': 12, 'CData2': 14}



class Converter:
    def convertXMLToX12(self, sample_xml):
        # claim_json = request.data
        # print "claim_json",claim_json
        output_x12 = ''
        try:
            stream = cStringIO.StringIO(sample_xml)
            input_source = libxml2.inputBuffer(stream)
            reader = input_source.newTextReader(sample_xml)
            ret = reader.Read()
            found_text = False
            # ele_id = ''
            # subele_id = ''
            subele_term = ''
            # seg_data = type(pyx12.segment.Segment('ISA', '~', '*', ':'))
            # print "reader", reader
            while ret == 1:
                tmpNodeType = reader.NodeType()

                if tmpNodeType == NodeType['element_start']:
                    found_text = False
                    cur_name = reader.Name()
                    if cur_name == 'seg':
                        while reader.MoveToNextAttribute():
                            if reader.Name() == 'id':
                                #fd_out.write(reader.Value())
                                seg_data = pyx12.segment.Segment(reader.Value(), \
                                    '~', '*', ':')
                                # print "seg_data", seg_data
                    elif cur_name == 'ele':
                        while reader.MoveToNextAttribute():
                            if reader.Name() == 'id':
                                ele_id = reader.Value()
                                # print "ele_id", type(ele_id)
                    #elif cur_name == 'comp':
                    #    comp = []
                    elif cur_name == 'subele':
                        while reader.MoveToNextAttribute():
                            if reader.Name() == 'id':
                                subele_id = reader.Value()
                                # print "subele_id", type(subele_id)
                elif tmpNodeType == NodeType['CData2']:
                    if cur_name == 'ele':
                        seg_data.set(ele_id, reader.Value().replace('\n', ''))
                        found_text = True
                    elif cur_name == 'subele':
                        seg_data.set(subele_id, reader.Value().replace('\n', ''))
                        found_text = True
                elif tmpNodeType == NodeType['text']:
                    if cur_name == 'ele':
                        if ele_id == 'ISA16':
                            subele_term = ':'
                        else:
                            seg_data.set(ele_id, reader.Value())
                        found_text = True
                    elif cur_name == 'subele':
                        #comp.set(subele_id, reader.Value())
                        seg_data.set(subele_id, reader.Value())
                        found_text = True
                elif tmpNodeType == NodeType['element_end']:
                    cur_name = reader.Name()
                    if cur_name == 'seg':
                        if seg_data.get_seg_id() == 'ISA':
                            seg_str = seg_data.format()
                            output_x12 += seg_str[:-1] + seg_str[-3] + subele_term + seg_str[-1]
                        else:
                            output_x12 += seg_data.format()
                        # output_x12 += '\n'
                    elif cur_name == 'ele':
                        if not found_text:
                            seg_data.set(ele_id, '')
                            found_text = True
                        ele_id = None
                    elif cur_name == 'subele' and not found_text:
                        #comp.append('')
                        seg_data.set(subele_id, '')
                        found_text = True
                        subele_id = None
                    elif cur_name == 'comp':
                        #seg_data.append(string.join(comp, ':'))
                        subele_id = None
                    cur_name = None
                ret = reader.Read()

        except:
            return False
        return output_x12




#     def convertX12ToXML(self,param, src_file, fd_997, fd_html,
#         fd_xmldoc=None,
#         xslt_files = []):
#         map_path = param.get('map_path')
#         logger = logging.getLogger('pyx12')
#         logger.debug('MAP PATH: %s' % (map_path))
#         errh = error_handler.err_handler()
#         # errh = errh_xml.errh_list()
#         # errh.register()
#         # param.set('checkdate', None)
#
#         # Get X12 DATA file
#         try:
#             src = x12file.X12file(src_file)
#         except pyx12.errors.X12Error:
#             logger.error('"%s" does not look like an X12 data file' % (src_file))
#             return False
#
#         # Get Map of Control Segments
#         map_file = 'x12.control.00401.xml'
#         control_map = map_if.load_map_file(os.path.join(map_path, map_file), param)
#         map_index_if = map_index.map_index(os.path.join(map_path, 'maps.xml'))
#         node = control_map.getnodebypath('/ISA_LOOP/ISA')
#         walker = walk_tree()
#         icvn = fic = vriic = tspc = None
#         # XXX Generate TA1 if needed.
#
#         if fd_html:
#             html = error_html.error_html(errh, fd_html, src.get_term())
#             html.header()
#             err_iter = error_handler.err_iter(errh)
#         if fd_xmldoc:
#             logger.debug('xmlout: %s' % (param.get('xmlout')))
#             if param.get('xmlout') == 'simple':
#                 import pyx12.x12xml_simple as x12xml_simple
#                 xmldoc = x12xml_simple.x12xml_simple(fd_xmldoc,
#                                                      param.get('simple_dtd'))
#             elif param.get('xmlout') == 'idtag':
#                 import pyx12.x12xml_idtag as x12xml_idtag
#                 xmldoc = x12xml_idtag.x12xml_idtag(fd_xmldoc,
#                                                    param.get('idtag_dtd'))
#             elif param.get('xmlout') == 'idtagqual':
#                 import pyx12.x12xml_idtagqual as x12xml_idtagqual
#                 xmldoc = x12xml_idtagqual.x12xml_idtagqual(fd_xmldoc,
#                                                            param.get('idtagqual_dtd'))
#             else:
#                 import pyx12.x12xml_simple as x12xml_simple
#                 xmldoc = x12xml_simple.x12xml_simple(fd_xmldoc,
#                                                      param.get('simple_dtd'))
#
#         # basedir = os.path.dirname(src_file)
#         # erx = errh_xml.err_handler(basedir=basedir)
#
#         valid = True
#         for seg in src:
#             # find node
#             orig_node = node
#
#             if seg.get_seg_id() == 'ISA':
#                 node = control_map.getnodebypath('/ISA_LOOP/ISA')
#             elif seg.get_seg_id() == 'GS':
#                 node = control_map.getnodebypath('/ISA_LOOP/GS_LOOP/GS')
#             else:
#                 try:
#                     node = walker.walk(node, seg, errh, src.get_seg_count(), \
#                                        src.get_cur_line(), src.get_ls_id())
#                 except errors.EngineError:
#                     logger.error('Source file line %i' % (src.get_cur_line()))
#                     raise
#             if node is None:
#                 node = orig_node
#             else:
#                 if seg.get_seg_id() == 'ISA':
#                     errh.add_isa_loop(seg, src)
#                     icvn = seg.get_value('ISA12')
#                     errh.handle_errors(src.pop_errors())
#                 elif seg.get_seg_id() == 'IEA':
#                     errh.handle_errors(src.pop_errors())
#                     errh.close_isa_loop(node, seg, src)
#                     # Generate 997
#                     # XXX Generate TA1 if needed.
#                 elif seg.get_seg_id() == 'GS':
#                     fic = seg.get_value('GS01')
#                     vriic = seg.get_value('GS08')
#                     map_file_new = map_index_if.get_filename(icvn, vriic, fic)
#                     if map_file != map_file_new:
#                         map_file = map_file_new
#                         if map_file is None:
#                             raise pyx12.errors.EngineError, "Map not found.  icvn=%s, fic=%s, vriic=%s" % \
#                                                             (icvn, fic, vriic)
#                         cur_map = map_if.load_map_file(map_file, param, xslt_files)
#                         logger.debug('Map file: %s' % (map_file))
#                         apply_loop_count(orig_node, cur_map)
#                         reset_isa_counts(cur_map)
#                     reset_gs_counts(cur_map)
#                     node = cur_map.getnodebypath('/ISA_LOOP/GS_LOOP/GS')
#                     errh.add_gs_loop(seg, src)
#                     errh.handle_errors(src.pop_errors())
#                 elif seg.get_seg_id() == 'BHT':
#                     if vriic in ('004010X094', '004010X094A1'):
#                         tspc = seg.get_value('BHT02')
#                         logger.debug('icvn=%s, fic=%s, vriic=%s, tspc=%s' % \
#                                      (icvn, fic, vriic, tspc))
#                         map_file_new = map_index_if.get_filename(icvn, vriic, fic, tspc)
#                         logger.debug('New map file: %s' % (map_file_new))
#                         if map_file != map_file_new:
#                             map_file = map_file_new
#                             if map_file is None:
#                                 raise pyx12.errors.EngineError, "Map not found.  icvn=%s, fic=%s, vriic=%s, tspc=%s" % \
#                                                                 (icvn, fic, vriic, tspc)
#                             cur_map = map_if.load_map_file(map_file, param, xslt_files)
#                             logger.debug('Map file: %s' % (map_file))
#                             apply_loop_count(node, cur_map)
#                             node = cur_map.getnodebypath('/ISA_LOOP/GS_LOOP/ST_LOOP/HEADER/BHT')
#                     errh.add_seg(node, seg, src.get_seg_count(), \
#                                  src.get_cur_line(), src.get_ls_id())
#                     errh.handle_errors(src.pop_errors())
#                 elif seg.get_seg_id() == 'GE':
#                     errh.handle_errors(src.pop_errors())
#                     errh.close_gs_loop(node, seg, src)
#                 elif seg.get_seg_id() == 'ST':
#                     errh.add_st_loop(seg, src)
#                     errh.handle_errors(src.pop_errors())
#                 elif seg.get_seg_id() == 'SE':
#                     errh.handle_errors(src.pop_errors())
#                     errh.close_st_loop(node, seg, src)
#                 else:
#                     errh.add_seg(node, seg, src.get_seg_count(), \
#                                  src.get_cur_line(), src.get_ls_id())
#                     errh.handle_errors(src.pop_errors())
#
#                 # errh.set_cur_line(src.get_cur_line())
#                 valid &= node.is_valid(seg, errh)
#                 # erx.handleErrors(src.pop_errors())
#                 # erx.handleErrors(errh.get_errors())
#                 # errh.reset()
#
#             if fd_html:
#                 if node is not None and node.is_first_seg_in_loop():
#                     html.loop(node.get_parent())
#                 err_node_list = []
#                 while True:
#                     try:
#                         err_iter.next()
#                         err_node = err_iter.get_cur_node()
#                         err_node_list.append(err_node)
#                     except pyx12.errors.IterOutOfBounds:
#                         break
#                 html.gen_seg(seg, src, err_node_list)
#
#             if fd_xmldoc:
#                 xmldoc.seg(node, seg)
#
#                 # erx.Write(src.cur_line)
#
#         # erx.handleErrors(src.pop_errors())
#         src.cleanup()  # Catch any skipped loop trailers
#         errh.handle_errors(src.pop_errors())
#         # erx.handleErrors(src.pop_errors())
#         # erx.handleErrors(errh.get_errors())
#
#         if fd_html:
#             html.footer()
#             del html
#
#         if fd_xmldoc:
#             del xmldoc
#
#         # visit_debug = error_debug.error_debug_visitor(sys.stdout)
#         # errh.accept(visit_debug)
#
#         # If this transaction is not a 997, generate one.
#         if not (vriic == '004010' and fic == 'FA'):
#             if fd_997:
#                 visit_997 = error_999.error_999_visitor(fd_997, src.get_term())
#                 errh.accept(visit_997)
#                 del visit_997
#         del node
#         del src
#         del control_map
#         del cur_map
#         try:
#             if not valid or errh.get_error_count() > 0:
#                 return False
#             else:
#                 return True
#         except:
#             print errh
#             return False
#
# def apply_loop_count(self,orig_node, new_map):
#     """
#     Apply loop counts to current map
#     """
#     logger = logging.getLogger('pyx12')
#     ct_list = []
#     orig_node.get_counts_list(ct_list)
#     for (path, ct) in ct_list:
#         try:
#             curnode = new_map.getnodebypath(path)
#             curnode.set_cur_count(ct)
#         except errors.EngineError:
#             logger.error('getnodebypath failed:  path "%s" not found' % path)
#
# def reset_isa_counts(self,cur_map):
#     cur_map.getnodebypath('/ISA_LOOP').set_cur_count(1)
#     cur_map.getnodebypath('/ISA_LOOP/ISA').set_cur_count(1)
#
# def reset_gs_counts(elf,cur_map):
#     cur_map.getnodebypath('/ISA_LOOP/GS_LOOP').reset_cur_count()
#     cur_map.getnodebypath('/ISA_LOOP/GS_LOOP').set_cur_count(1)
#     cur_map.getnodebypath('/ISA_LOOP/GS_LOOP/GS').set_cur_count(1)