import os

def setup_cli_dir(project_dir: str, project_name: str):
    os.chdir(project_dir)
    os.system('mkdir src')
    os.chdir('src')
    os.system('touch __init__.py')
    os.system(f"mkdir {project_name}")
    os.chdir(project_name)
    os.system('touch __init__.py')
    os.mkdir('core')
    os.system('touch __init__.py')
    os.system(f"touch {project_name}.py")
    os.system(f'echo "import click" >> {project_name}.py')
    os.system(f'echo "" >> {project_name}.py')
    os.system(f'echo "@click.command()" >> {project_name}.py')
    os.system(f'echo "def main():" >> {project_name}.py')
    os.system(f'echo "    print(\'Hello, world!\')" >> {project_name}.py')
    os.system(f'echo "" >> {project_name}.py')
    os.system(f'echo "if __name__ == \'__main__\':" >> {project_name}.py')
    os.system(f'echo "    main()" >> {project_name}.py')
