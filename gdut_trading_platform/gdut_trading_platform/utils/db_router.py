'''
class MasterSlaveDBRouter(object):
    """���ݿ����Ӷ�д����·��"""

    def db_for_read(self, model, **hints):
        """�����ݿ�"""
        return "slave"

    def db_for_write(self, model, **hints):
        """д���ݿ�"""
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        """�Ƿ����й�������"""
        return True
'''
