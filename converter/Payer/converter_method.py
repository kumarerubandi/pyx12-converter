import pyx12.params
import pyx12.xmlx12_simple
import libxml2
import cStringIO
import pyx12.segment
import subprocess
import os
import tempfile

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

    def validate_x12(self,x12_data):
        # print "x12-------",x12_data
        open("x12_request", 'w').close()
        f = open("x12_request", "a")
        f.write(x12_data)
        f.close()
        # result = subprocess.check_output(['x12valid', 'x12_request'])
        # result = os.system('x12valid x12_request')
        # print "result--------"
        # print result
        with tempfile.TemporaryFile() as tempf:
            proc = subprocess.Popen(['x12valid', 'x12_request'], stdout=tempf)
            proc.wait()
            tempf.seek(0)
            # print "nnnnnnnnnnnnnnnnnn"
            print tempf.read()
        return True

    # def x12n_document(self,src):
    #     logger = logging.getLogger('pyx12')
    #     param = pyx12.params.params(None)
    #     param.set('exclude_external_codes', ','.join([]))
    #     errh = pyx12.error_handler.err_handler()
    #     map_file = 'x12.control.00501.xml'
    #     control_map = pyx12.map_if.load_map_file(map_file, param, None)
    #     map_index_if = pyx12.map_index.map_index(None)
    #     node = control_map.getnodebypath('/ISA_LOOP/ISA')
    #     walker = walk_tree()
    #     icvn = fic = vriic = tspc = None
    #     cur_map = None
    #     valid = True
    #     for seg in src:
    #         # find node
    #         print "seg------",seg
    #         orig_node = node
    #         if False:
    #             print('--------------------------------------------')
    #             print(seg)
    #             print('--------------------------------------------')
    #             print('------- counters before --------')
    #             print(walker.counter._dict)
    #         if seg.get_seg_id() == 'ISA':
    #             node = control_map.getnodebypath('/ISA_LOOP/ISA')
    #             walker.forceWalkCounterToLoopStart('/ISA_LOOP', '/ISA_LOOP/ISA')
    #         elif seg.get_seg_id() == 'GS':
    #             node = control_map.getnodebypath('/ISA_LOOP/GS_LOOP/GS')
    #             walker.forceWalkCounterToLoopStart('/ISA_LOOP/GS_LOOP', '/ISA_LOOP/GS_LOOP/GS')
    #         else:
    #             # from the current node, find the map node matching the segment
    #             # keep track of the loops traversed
    #             try:
    #                 (node, pop_loops, push_loops) = walker.walk(node, seg, errh,
    #                                                             src.get_seg_count(), src.get_cur_line(),
    #                                                             src.get_ls_id())
    #             except pyx12.errors.EngineError:
    #                 logger.error('Source file line %i' % (src.get_cur_line()))
    #                 raise
    #
    #         if False:
    #             print('------- counters after --------')
    #             print(walker.counter._dict)
    #         if node is None:
    #             node = orig_node
    #         else:
    #             # print "seg.get_seg_id()------",seg.get_seg_id()
    #             if seg.get_seg_id() == 'ISA':
    #                 errh.add_isa_loop(seg, src)
    #                 icvn = seg.get_value('ISA12')
    #                 errh.handle_errors(src.pop_errors())
    #             elif seg.get_seg_id() == 'IEA':
    #                 errh.handle_errors(src.pop_errors())
    #                 errh.close_isa_loop(node, seg, src)
    #                 # Generate 997
    #                 # XXX Generate TA1 if needed.
    #             elif seg.get_seg_id() == 'GS':
    #                 fic = seg.get_value('GS01')
    #                 vriic = seg.get_value('GS08')
    #                 map_file_new = map_index_if.get_filename(icvn, vriic, fic)
    #                 if map_file != map_file_new:
    #                     map_file = map_file_new
    #                     if map_file is None:
    #                         err_str = "Map not found.  icvn={}, fic={}, vriic={}".format(icvn, fic, vriic)
    #                         raise pyx12.errors.EngineError(err_str)
    #                     cur_map = pyx12.map_if.load_map_file(map_file, param, None)
    #                     src.check_837_lx = True if cur_map.id == '837' else False
    #                     logger.debug('Map file: %s' % (map_file))
    #                 node = cur_map.getnodebypath('/ISA_LOOP/GS_LOOP/GS')
    #                 errh.add_gs_loop(seg, src)
    #                 errh.handle_errors(src.pop_errors())
    #             elif seg.get_seg_id() == 'BHT':
    #                 if vriic in ['004010X094', '004010X094A1', '005010X217']:
    #                     tspc = seg.get_value('BHT02')
    #                     logger.debug('icvn=%s, fic=%s, vriic=%s, tspc=%s' %
    #                                  (icvn, fic, vriic, tspc))
    #                     print "icvn, vriic, fic, tspc", icvn, vriic, fic, tspc
    #                     map_file_new = map_index_if.get_filename(icvn, vriic, fic, tspc)
    #                     logger.debug('New map file: %s' % (map_file_new))
    #                     print "mapfile------", map_file_new
    #                     if map_file != map_file_new:
    #                         map_file = map_file_new
    #                         if map_file is None:
    #                             err_str = "Map not found.  icvn={}, fic={}, vriic={}, tspc={}".format(
    #                                 icvn, fic, vriic, tspc)
    #                             raise pyx12.errors.EngineError(err_str)
    #                         cur_map = pyx12.map_if.load_map_file(map_file, param, None)
    #                         src.check_837_lx = True if cur_map.id == '837' else False
    #                         logger.debug('Map file: %s' % (map_file))
    #                         # apply_loop_count(node, cur_map)
    #                         node = cur_map.getnodebypath('/ISA_LOOP/GS_LOOP/ST_LOOP/HEADER/BHT')
    #                 errh.add_seg(node, seg, src.get_seg_count(), src.get_cur_line(), src.get_ls_id())
    #                 errh.handle_errors(src.pop_errors())
    #             elif seg.get_seg_id() == 'GE':
    #                 errh.handle_errors(src.pop_errors())
    #                 errh.close_gs_loop(node, seg, src)
    #             elif seg.get_seg_id() == 'ST':
    #                 errh.add_st_loop(seg, src)
    #                 errh.handle_errors(src.pop_errors())
    #             elif seg.get_seg_id() == 'SE':
    #                 errh.handle_errors(src.pop_errors())
    #                 errh.close_st_loop(node, seg, src)
    #             else:
    #                 errh.add_seg(node, seg, src.get_seg_count(), src.get_cur_line(), src.get_ls_id())
    #                 errh.handle_errors(src.pop_errors())
    #
    #             valid &= node.is_valid(seg, errh)
    #
    #     try:
    #         if not valid or errh.get_error_count() > 0:
    #             return False
    #         else:
    #             return True
    #     except Exception:
    #         print(errh)
    #         return False
