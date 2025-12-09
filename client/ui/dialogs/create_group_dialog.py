"""Dialog for creating a new chat group."""
from typing import List, Dict, Tuple
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QListWidget, QListWidgetItem, 
                             QDialogButtonBox)
from PyQt5.QtCore import Qt


class CreateGroupDialog(QDialog):
    """Dialog to create a new chat group."""
    
    def __init__(self, contacts: List[Dict], parent=None):
        """
        Initialize create group dialog.
        
        Args:
            contacts: List of contact dictionaries
            parent: Parent widget
        """
        super().__init__(parent)
        self.contacts = contacts
        self.setWindowTitle("Tạo nhóm chat mới")
        self.setMinimumSize(400, 500)
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        name_layout = QHBoxLayout()
        name_label = QLabel("Tên nhóm:")
        self.group_name_input = QLineEdit()
        self.group_name_input.setPlaceholderText("Nhập tên cho nhóm của bạn...")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.group_name_input)
        layout.addLayout(name_layout)

        members_label = QLabel("Chọn thành viên:")
        layout.addWidget(members_label)

        self.members_list = QListWidget()
        self.members_list.setSelectionMode(QListWidget.MultiSelection)
        for contact in self.contacts:
            item = QListWidgetItem(f"{contact['display_name']} (@{contact['username']})")
            item.setData(Qt.UserRole, contact['id'])
            self.members_list.addItem(item)
        layout.addWidget(self.members_list)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_group_data(self) -> Tuple[str, List[int]]:
        """
        Get group information and selected member IDs.
        
        Returns:
            Tuple of (group_name, member_ids)
        """
        group_name = self.group_name_input.text().strip()
        selected_items = self.members_list.selectedItems()
        member_ids = [item.data(Qt.UserRole) for item in selected_items]
        
        return group_name, member_ids

