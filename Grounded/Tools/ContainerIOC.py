import re
import yaml
from dependency_injector import providers


class ContainerIOC:
    """
    Cette classe permet de faire le lien entre la ligne de commande et le code. Il s'agit d'un conteneur d'inversion de
    dépendance. Celle-ci est fortement inspiré du conteneur builder de Symfony (framework php).
    Cette classe permet l'instanciation de modules dynamiquement à partir de la configuration par défaut
    de l'application stockée dans un fichier yaml
    """

    def __init__(self, config_file: str):
        """
        Constructeur de la classe ContainerIOC, cette méthode prend en paramètre un fichier yaml contenant la
        configuration par défaut de l'application

        Args:
            config_file (str): un fichier de configuration au format yaml
        """
        self.container: dict = load_from_yaml(config_file)

    def get(self, name: str, kwargs_dict: dict = {}, **kwargs):
        """
        Cette fonction permet d'accéder à différentes variables stockées dans le conteneur. Elle se charge également
        de l'instantiation des différents modules à partir de valeurs par défaut contenu dans un fichier yaml.
        Ces valeurs par défaut peuvent être écrasé par l'utilisateur s'il les spécifie dans les paramètres kwargs.

        Args:
            name (str): nom du service/variable souhaité
            kwargs_dict (dict): arguments utilisés lors de l'instanciation d'un service
            **kwargs : arguments utilisés lors de l'instanciation d'un service

        Returns: Une variable/Un service

        """
        # Si le conteneur ne contient pas l'attribut on renvoie une erreur
        attr = self.container.get(name)
        if attr is None:
            raise DependencyNotFoundError(name)

        if isinstance(attr, providers.Factory):
            args = kwargs_dict | kwargs
            if not set(args.keys()) <= set(attr.kwargs['args'].keys()):
                raise Exception(f"bad arguments was given to create {name} tool")
            for key, value in attr.kwargs['args'].items():
                if isinstance(value, str):
                    attr.kwargs['args'][key] = self._resolver(value)
            attr.kwargs['args'].update(args)
            return attr()
        else:
            if isinstance(attr, str):
                return self._resolver(attr)
            else:
                return attr

    def set(self, name, value):
        """
        Cette méthode permet d'insérer un nouvel objet dans le conteneur.

        Args:
            name: nom de l'objet qui sera utilisé par la suite pour y accéder
            value: objet à insérer
        """
        self.container[name] = value

    def _resolver(self, string: str) -> str:
        """
        Méthode interne de la classe ContainerIOC. Elle permet de résoudre l'inclusion de variables dans des
        string par un appel récursif.

        Returns:
            str : Une chaîne de caractère dont les variables inclues ont été inséré
        """
        def replace_match(match):
            # Retourne le remplacement correspondant
            return self.container.get(match.group(1), match.group(0))

        # Pattern pour trouver les segments encadrés par des %
        pattern = r"%([^%]+)%"
        # Remplace les segments
        nouvelle_chaine = re.sub(pattern, replace_match, string)

        return nouvelle_chaine


class DependencyNotFoundError(Exception):
    def __init__(self, dependency_name):
        self.dependency_name = dependency_name
        self.message = f"La dépendance '{self.dependency_name}' n'est pas enregistrée dans le conteneur."
        super().__init__(self.message)


def load_from_yaml(file_path) -> dict:
    with open(file_path, 'r') as yaml_file:
        services_data = yaml.safe_load(yaml_file)

    yaml_content = services_data.get('values')

    for service_name, service_data in services_data.get('tools', {}).items():
        class_path = service_data.get('class')
        args = service_data.get('arguments', {})
        provider = providers.Factory(create_instance, class_path=class_path, args=args)
        yaml_content[service_name] = provider

    return yaml_content


def create_instance(class_path, args):
    parts = class_path.split('.')
    module_path = '.'.join(parts[:-1])
    class_name = parts[-1]
    module = __import__(module_path, fromlist=[class_name])
    clazz = getattr(module, class_name)
    return clazz(**args)
