import uuid
from sqlalchemy import UUID, Column, Integer, String, ForeignKey, Boolean, DateTime, Enum, func
from sqlalchemy.orm import relationship
from blitzkrieg.project_management.db.models.Base import Base
class Project(Base):
    __tablename__ = 'project'
    __table_args__ = {'schema': 'project_management'}

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String)
    github_repo = Column(String)  # GitHub repository URL
    directory_path = Column(String)  # Path to the project directory
    is_deployed = Column(Boolean, default=False)  # Whether the project is deployed
    deployment_date = Column(DateTime)  # The date and time of deployment
    pip_package_name = Column(String)  # The name of the pip package
    parent_id = Column(UUID, ForeignKey('project_management.project.id'))  # ID of the parent project
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    short_description = Column(String, nullable=True)  # Short description of the project
    description = Column(String, nullable=True)  # Description of the project
    # project_type should be an Enum of python_cli, pyo3_rust_extension, etc.
    project_type = Column(Enum('python_cli', 'pyo3_rust_extension', name='project_type_enum'))
    # Relationship to self to allow nested projects
    children = relationship('Project', backref='parent', remote_side=[id])
