from .setup import *
from .task_xml import Task


class ModuleXml(PluginModuleBase):
    def __init__(self, P):
        super(ModuleXml, self).__init__(P, name='xml', first_menu='setting')
        self.db_default = {
            f'{self.name}_db_version' : '1',
            f'{self.name}_auto_start' : 'False',
            f'{self.name}_interval' : '30 0/12 * * *',
            f'{self.name}_updated_tvheadend' : '',
            f'{self.name}_updated_alive' : '',
            f'{self.name}_updated_hdhomerun' : '',
        }

    def process_menu(self, page, req):
        try:
            arg = P.ModelSetting.to_dict()
            arg['sub'] = self.name
            if page == 'setting':
                for tmp in ['tvheadend', 'alive', 'hdhomerun', 'all']:
                    arg[tmp] = ToolUtil.make_apikey_url(f'/{P.package_name}/api/{self.name}/{tmp}')
            return render_template(f'{self.P.package_name}_{self.name}_{page}.html', arg=arg)
        except Exception as e:
            logger.error(f"Exception:{str(e)}")
            logger.error(traceback.format_exc())
            return render_template('sample.html', title=f"PluginModuleBase-process_menu{self.P.package_name}/{self.name}/{page}")
        
    def process_command(self, command, arg1, arg2, arg3, req):
        try:
            ret = {}
            if command == 'make':
                self.task_interface(req.form['arg1'], 'manual')
                ret = {'ret':'success', 'msg':'생성을 시작합니다.'}
            elif command == 'epg_time':
                tmp = P.ModelSettingDATA.get('updated_time')
                ret = {'ret':'success', 'msg':tmp}
            elif command == 'celery_epg_time':
                if F.config['use_celery']:
                    result = Task.updated_time.apply_async()
                    updated_time = result.get()
                else:
                    updated_time = Task.updated_time()
                ret = {'ret':'success', 'msg':updated_time}

            return jsonify(ret)
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            return jsonify({'ret':'danger', 'msg':str(e)})
    
    def process_api(self, sub, req):
        try:
            output_filepath = Task.get_output_filepath(sub)
            if not os.path.exists(output_filepath):
                self.task_interface(sub, 'manual').join()
            return send_file(output_filepath, mimetype='application/xml')
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            

    def scheduler_function(self):
        self.task_interface('alive', 'scheduler').join()
        self.task_interface('hdhomerun', 'scheduler').join()
        self.task_interface('tvheadend', 'scheduler').join()

    #########################################################

    def task_interface(self, *args):
        def func(*args):
            func = Task.start
            time.sleep(1)
            if F.config['use_celery']:
                result = Task.start.apply_async(args)
                ret = result.get()
            else:
                ret = Task.start(*args)
        
                logger.info(f"args:{args}")
        def func2(*args):
            logger.debug(f'dummy {args}')

        need_make = 0
        plugin = args[0]
        mode = args[1]
        Task.git_pull()
        if mode == 'manual':
            need_make = 1
        output_filepath = Task.get_output_filepath(plugin)
        if need_make == 0 and os.path.exists(output_filepath) == False:
            need_make = 2
        if need_make == 0:
            time_str = ModelSetting.get(f"user_updated_{plugin}")
            if time_str == '':
                need_make = 3
            else:
                update_dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                epg_dt = datetime.strptime(P.ModelSettingDATA.get('updated_time'), '%Y-%m-%d %H:%M:%S')
                logger.info(f"update_dt : {update_dt}")
                logger.info(f"epg_dt : {epg_dt}")
                if update_dt < epg_dt:
                    need_make = 4

        logger.info(f"EPG 생성 : {plugin} {mode} {need_make}")
        if need_make == 0:
            function = func2
        else:
            function = func

        th = threading.Thread(target=function, args=args)
        th.setDaemon(True)
        th.start()
        return th
        
