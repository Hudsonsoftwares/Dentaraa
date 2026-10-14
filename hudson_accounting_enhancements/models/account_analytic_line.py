from odoo import models, api
from lxml import etree
from lxml.builder import E

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    def _patch_view(self, arch, view, view_type):
        arch, view = super()._patch_view(arch, view, view_type)
        if self.env['account.analytic.plan'].has_access('read'):
            project_plan, other_plans = self.env['account.analytic.plan']._get_all_plans()
            all_plans = project_plan + other_plans

            if view_type == 'search':
                account_filter_node = arch.find('.//filter[@name="account_id"]')
                if account_filter_node is not None:
                    # Make sure root project plan has proper label
                    if project_plan:
                        account_filter_node.set('string', project_plan.name or 'Project Plan')
                    
                    # Ensure all other plans have filters with their exact plan names
                    curr_node = account_filter_node
                    for plan in other_plans:
                        fname = plan._column_name()
                        existing_node = arch.find(f'.//filter[@name="{fname}"]')
                        if existing_node is not None:
                            existing_node.set('string', plan.name)
                            curr_node = existing_node
                        else:
                            new_filter = E.filter(
                                name=fname,
                                string=plan.name,
                                context=f"{{'group_by': '{fname}'}}"
                            )
                            curr_node.addnext(new_filter)
                            curr_node = new_filter

            elif view_type == 'pivot':
                # Ensure all analytic plan fields are present as groupable fields in the pivot view
                for plan in all_plans:
                    fname = plan._column_name()
                    if fname in self._fields:
                        existing_field = arch.find(f'.//field[@name="{fname}"]')
                        if existing_field is None:
                            arch.append(E.field(name=fname, string=plan.name))

        return arch, view
