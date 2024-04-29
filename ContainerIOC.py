import yaml
from dependency_injector import containers, providers


class ContainerIOC:
    def __init__(self, config_file: str):
        self.container = load_services_from_yaml(config_file)

    def get(self, name, **kwargs):
        provider = getattr(self.container, name)
        provider.kwargs['args'].update(kwargs)
        return provider()


class ServiceContainer(containers.DeclarativeContainer):
    pass


def load_services_from_yaml(file_path):
    with open(file_path, 'r') as yaml_file:
        services_data = yaml.safe_load(yaml_file)

    for service_name, service_data in services_data.get('tools', {}).items():
        class_path = service_data.get('class')
        args = service_data.get('arguments', {})
        provider = providers.Factory(create_instance, class_path=class_path, args=args)
        setattr(ServiceContainer, service_name, provider)

    return ServiceContainer


def create_instance(class_path, args):
    parts = class_path.split('.')
    module_path = '.'.join(parts[:-1])
    class_name = parts[-1]
    module = __import__(module_path, fromlist=[class_name])
    clazz = getattr(module, class_name)
    return clazz(**args)
