from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings


class FastDFSStorage(Storage):
    """⾃定义Django的⽂件存储系统"""
    def __init__(self, client_conf=None, base_url=None):  # 对storage，参数必须要有默认值注意
        # 为什么这里要加参数client_conf与base_url，因为如果我们在后面代码中不想用settings配置中指定的，就需要输入这个参数
        """
        初始化⽂件存储对象的构造⽅法
        :param client_conf: client.conf的⽂件绝对路径
        :param base_url: 下载⽂件时的域名(ip:端⼝)
        """
        # if client_conf == None:
        # self.client = settings.FDFS_CLIENT_CONF
        # self.client = client_conf
        # 如果client_conf参数为None,就读取or后⾯的值
        self.client_conf = client_conf or settings.FDFS_CLIENT_CONF   # 配置 or 指定 （常见写法）
        self.base_url = base_url or settings.FDFS_BASE_URL

    def _open(self, name, mode='rb'):
        """
        存储类⽤于打开⽂件: 因为必须实现,但是此处是⽂件存储不需要打开⽂件,所以重写之后什么也不做pass
        :param name: # 要打开的⽂件的名字
        :param mode: # 打开模式,read bytes
        :return: None
        """
        pass

    def _save(self, name, content):
        """
        实现⽂件存储: 在这个⽅法⾥⾯将⽂件转存到FastDFS服务器
        :param name: 要存储的⽂件名字
        :param content: 要存储的⽂件对象, File类型的对象,将来使⽤content.read()读取对象中的⽂件⼆进制
        :return: file_id
        """
        # 创建对接fastDFS 的客户端对象

        # client = Fdfs_client('gdut_trading_platform/utils/fastdfs/client.conf') # 另外，在代码中写死都是不利的行为，统一配置才好
        # client = Fdfs_client(settings.FDFS_CLIENT_CONF)
        client = Fdfs_client(self.client_conf)
        # 将⽂件转存到fdfs
        # ret = client.upload_by_filename('D:/image/image_source_two/cpu1.jpg')    # 规范的开发，并不写死，而是统一配置
        ret = client.upload_by_buffer(content.read())
        # 判断⽂件上传是否成功

        if ret.get('Status') != 'Upload successed.':
            raise Exception('upload file failed')
        # 能够执⾏到这⾥说明上传成功

        file_id = ret.get('Remote file_id')
        # 在⾃定义了⽂件存储系统之后,我们只需要返回file_id即可
        # 将来⽂件存储系统会'⾃动'的将file_id 存储到对应的ImageFiled字段中
        # file_id == 'group1\\M00/00/00/wKjvZGOIHqmAWfUSAAFew6WVUo0557.jpg'
        return file_id

    def exists(self, name):
        """
        判断要上传的⽂件是否已存在,判断storage中是否已存储了该⽂件,如果存储了就不会再存储,如果没有存储就调⽤_save()
        :param name: 要判断的⽂件名字
        :return: True(⽂件存在) / False(⽂件不存在)
        """
        return False

    def url(self, name):
        """
        返回⽂件的绝对路径,下载图⽚时使⽤
        :param name: 要读取的⽂件名字 name == file_id
        :return: ⽂件绝对路径 http://192.168.239.100:8888/group1\\M00/00/00/wKjvZGOIHqmAWfUSAAFew6WVUo0557.jpg
        """
        # return 'http://192.168.239.100:8888/' + name
        return self.base_url + name
