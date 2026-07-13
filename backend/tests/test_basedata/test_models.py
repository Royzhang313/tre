"""BaseData 模块 —— ORM 模型结构测试"""

from app.modules.basedata.models import (
    Company,
    Enterprise,
    EnterpriseContact,
    Warehouse,
)


def _ann(cls: type) -> dict:
    result: dict = {}
    for base in reversed(cls.__mro__):
        result.update(getattr(base, "__annotations__", {}))
    return result


class TestEnterprise:
    """企业"""

    def test_tablename(self):
        assert Enterprise.__tablename__ == "basedata_enterprises"

    def test_has_name(self):
        assert "name" in _ann(Enterprise)

    def test_has_enterprise_type(self):
        assert "enterprise_type" in _ann(Enterprise)

    def test_has_is_active(self):
        assert "is_active" in _ann(Enterprise)


class TestEnterpriseContact:
    """企业联系人"""

    def test_tablename(self):
        assert EnterpriseContact.__tablename__ == "basedata_enterprise_contacts"

    def test_has_name_mobile(self):
        ann = _ann(EnterpriseContact)
        assert "name" in ann
        assert "mobile" in ann


class TestCompany:
    """执行主体公司"""

    def test_tablename(self):
        assert Company.__tablename__ == "basedata_companies"

    def test_has_name(self):
        assert "name" in _ann(Company)

    def test_has_is_active(self):
        assert "is_active" in _ann(Company)


class TestWarehouse:
    """仓库"""

    def test_tablename(self):
        assert Warehouse.__tablename__ == "basedata_warehouses"

    def test_has_name(self):
        assert "name" in _ann(Warehouse)

    def test_has_is_active(self):
        assert "is_active" in _ann(Warehouse)
