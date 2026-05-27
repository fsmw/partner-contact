# Copyright 2014-2020 Camptocamp SA
# @author: Nicolas Bessi
# Copyright 2016-2020 Akretion (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestStreet3(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                tracking_disable=True,
            )
        )

    def test_partner(self):
        # Test address_format has been updated on existing countries
        us_country = self.env.ref("base.us")
        self.assertTrue("%(street3)s" in us_country.address_format)

        homer = self.env["res.partner"].create(
            {
                "name": "Homer Simpson",
                "city": "Springfield",
                "street": "742 Evergreen Terrace",
                "street2": "Donut Lane",
                "street3": "Tho",
                "country_id": us_country.id,
            }
        )

        # test synchro of street3 on create
        bart = self.env["res.partner"].create(
            {
                "name": "Bart Simpson",
                "parent_id": homer.id,
                "type": "contact",
            }
        )
        self.assertEqual(bart.street3, "Tho")
        bart.street3 = "\n\n"
        bart_address = bart._display_address()
        self.assertTrue("\n\n" not in bart_address)

        # test synchro of street3 on write
        homer.write({"street3": "in OCA we trust"})
        self.assertEqual(bart.street3, "in OCA we trust")

    def test_post_init_hook(self):
        from ..hooks import post_init_hook

        post_init_hook(self.env)
        us_country = self.env.ref("base.us")
        self.assertTrue("%(street3)s" in us_country.address_format)

    def test_uninstall(self):
        from ..hooks import uninstall_hook

        uninstall_hook(self.env)
        us_country = self.env.ref("base.us")
        self.assertTrue("%(street3)s" not in us_country.address_format)

    def test_onchange_parent_id_copies_street3(self):
        parent = self.env["res.partner"].create(
            {
                "name": "Parent Company",
                "street": "123 Main St",
                "street2": "Floor 2",
                "street3": "Suite 100",
                "city": "Springfield",
                "country_id": self.env.ref("base.us").id,
            }
        )
        child = self.env["res.partner"].new(
            {
                "parent_id": parent.id,
                "type": "contact",
                "name": "Child",
            }
        )
        result = child.onchange_parent_id()
        self.assertIn("value", result)
        self.assertEqual(result["value"].get("street3"), "Suite 100")
        self.assertEqual(result["value"].get("street2"), "Floor 2")
        self.assertEqual(result["value"].get("street"), "123 Main St")

    def test_onchange_parent_id_no_parent(self):
        child = self.env["res.partner"].new(
            {
                "type": "contact",
                "name": "Child",
            }
        )
        result = child.onchange_parent_id()
        self.assertIsNone(result)

    def test_onchange_parent_id_preserves_empty_parent(self):
        child = self.env["res.partner"].new(
            {
                "parent_id": self.env["res.partner"],
                "type": "contact",
                "name": "Child",
            }
        )
        result = child.onchange_parent_id()
        self.assertIsNone(result)

    def test_onchange_parent_id_extends_base_result(self):
        parent = self.env["res.partner"].create(
            {
                "name": "Parent Company",
                "street": "123 Main St",
                "city": "Springfield",
                "street3": "Suite 100",
                "country_id": self.env.ref("base.us").id,
            }
        )
        child = self.env["res.partner"].new(
            {
                "parent_id": parent.id,
                "type": "contact",
                "name": "Child",
            }
        )
        result = child.onchange_parent_id()
        self.assertIsNotNone(result)
        self.assertIn("value", result)
        self.assertIn("street3", result["value"])
        self.assertIn("street", result["value"])
        self.assertIn("city", result["value"])
