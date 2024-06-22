from .setup import *
from .task_maker import Task


class ModuleMaker(PluginModuleBase):
    def __init__(self, P):
        super(ModuleMaker, self).__init__(P, name='maker', first_menu='setting', scheduler_desc="epg_data.db 생성")
        self.db_default = {
            f'{self.name}_db_version' : '1',
            f'{self.name}_auto_start' : 'False',
            f'{self.name}_interval' : '120',
        }
    
    def process_command(self, command, arg1, arg2, arg3, req):
        try:
            ret = {}
            if command == 'sheet':
                ins = CliMakeSheet()
                arg1 = req.form['arg1']
                method_to_call = getattr(ins, arg1)
                result = method_to_call()
                logger.debug("종료")

            return jsonify(ret)
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            return jsonify({'ret':'danger', 'msg':str(e)})

    
    def scheduler_function(self):
        def func():
            func = Task.start
            time.sleep(1)
            if F.config['use_celery']:
                result = Task.start.apply_async()
                ret = result.get()
            else:
                ret = Task.start()
        
        if P.ModelSettingDATA.get('updated_time') == None:
            P.ModelSettingDATA.set('updated_time', '')

        th = threading.Thread(target=func, args=())
        th.setDaemon(True)
        th.start()
        th.join()
    
        
    #########################################################

    