# -*- encoding: utf-8 -*-

from typing import Generator, List, Optional, Tuple
from PyQt5.QtCore import Qt, QSize
from PyQt5 import QtWidgets


class EscapableQListWidget(QtWidgets.QListWidget):
    def keyPressEvent(self, event):
        super(EscapableQListWidget, self).keyPressEvent(event)
        if event.key() == Qt.Key.Key_Escape:
            self.clearSelection()


class UniqueLabelQListWidget(EscapableQListWidget):
    def mousePressEvent(self, event):
        super(UniqueLabelQListWidget, self).mousePressEvent(event)
        if not self.indexAt(event.pos()).isValid():
            self.clearSelection()

    def findRowIndexByLabel(self, label) -> Optional[int]:
        items_iter = self._find_items_by_label(label)
        item_indexes = list(idx for idx, _ in items_iter)
        return item_indexes[0] if len(item_indexes) > 0 else None

    def findItemsByLabel(self, label) -> List[Optional[QtWidgets.QListWidgetItem]]:
        items_iter = self._find_items_by_label(label)
        return list(item for _, item in items_iter)

    def _find_items_by_label(self, label):
        items_iter: Generator[
            Tuple[int, Optional[QtWidgets.QListWidgetItem]], None, None
        ] = ((row_idx, self.item(row_idx)) for row_idx in range(self.count()))

        items_iter = (
            (row_idx, item)
            for row_idx, item in items_iter
            if item is not None and item.data(Qt.ItemDataRole.UserRole) == label
        )

        return list(items_iter)

        # items: List[Optional[QtWidgets.QListWidgetItem]] = []
        # for row in range(self.count()):
        #     item: Optional[QtWidgets.QListWidgetItem] = self.item(row)
        #     if item is None:
        #         raise ValueError("item")
        #     if item.data(Qt.ItemDataRole.UserRole) == label:
        #         items.append(item)
        #         if get_row:
        #             return row
        # return items

    def createItemFromLabel(self, label):
        item = QtWidgets.QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, label)
        return item

    def setItemLabel(self, item, label, color=None):
        qlabel = QtWidgets.QLabel()
        if color is None:
            qlabel.setText(f"{label}")
        else:
            qlabel.setText(
                '<font color="#{:02x}{:02x}{:02x}">●</font> {} '.format(*color, label)
            )
        qlabel.setAlignment(Qt.AlignmentFlag.AlignBottom)

        # item.setSizeHint(qlabel.sizeHint())
        item.setSizeHint(QSize(25, 25))

        self.setItemWidget(item, qlabel)
