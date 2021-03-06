from tempfile import NamedTemporaryFile
from cm.app import UniverseApplication
from cm.clouds.ec2 import EC2Interface
from cm.clouds.cloud_config import CloudConfig

from yaml import dump
from contextlib import contextmanager
from mock import patch


class TestInterface(EC2Interface):

    def get_zone(self):
        return 'us-east-1a'

    def get_ami(self):
        return 'ami-l0cal1'


@contextmanager
def userdata(userdata={}):
    f = NamedTemporaryFile()
    try:
        dump(userdata, f)
        f.flush()
        with patch('cm.util.paths.USER_DATA_FILE', f.name):
            # Patch cloud interface to not actually make HTTP requests
            with patch.object(CloudConfig, 'get_cloud_interface') \
                    as mock_function:
                mock_function.return_value = TestInterface()
                yield
    finally:
        f.close()


def test_defaults():
    with userdata({}):
        app = UniverseApplication()
        # Test object store and volumes enabled by default.
        assert app.use_object_store
        assert app.use_volumes
        assert app.cloud_type == "ec2"


def test_disable_object_store():
    with userdata({"use_object_store": False}):
        app = UniverseApplication()
        assert not app.use_object_store


def test_no_opennebula_volumes():
    with userdata({"cloud_type": "opennebula"}):
        app = UniverseApplication()
        assert app.cloud_type == "opennebula"
        assert not app.use_volumes


def test_default_instance_types():
    with userdata({}):
        app = UniverseApplication()
        instance_types = app.config.instance_types
        assert instance_types[1] == ("t1.micro", "Micro")


def test_nectar_instance_types():
    with userdata({"cloud_name": "nectar"}):
        app = UniverseApplication()
        instance_types = app.config.instance_types
        assert len(instance_types) == 5
        assert instance_types[4][0] == "m1.xxlarge"


def test_dynamic_instance_types():
    TYPE1 = {"key": "z1.micro", "name": "REALLY SMALL"}
    TYPE2 = {"key": "z100.huge", "name": "HUGE"}
    with userdata({"instance_types": [TYPE1, TYPE2]}):
        app = UniverseApplication()
        instance_types = app.config.instance_types
        assert len(instance_types) == 2
        assert instance_types[0][0] == "z1.micro"
        assert instance_types[1][1] == "HUGE"
