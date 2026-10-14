/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { useService } from "@web/core/utils/hooks";
import { SelectCreateDialog } from "@web/views/view_dialogs/select_create_dialog";

export class BankRecActionDropdown extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
    }

    get record() {
        return this.props?.record;
    }

    get recordData() {
        return this.record?.data || {};
    }

    get isReconciled() {
        return Boolean(this.recordData.is_reconciled);
    }

    get hasMatches() {
        return Boolean(this.recordData.hudson_has_matches);
    }

    async onReconcile() {
        const domain = [
            ['account_id.reconcile', '=', true],
            ['reconciled', '=', false],
            ['move_id.state', '=', 'posted'],
            ['journal_id.type', 'not in', ['bank', 'cash']]
        ];
        
        let amount = this.recordData.amount;
        if (typeof amount === 'object' && amount !== null) {
            amount = amount.value !== undefined ? amount.value : (amount.amount !== undefined ? amount.amount : 0);
        }
        amount = typeof amount === 'number' ? amount : (parseFloat(amount) || 0.0);

        if (amount < 0) {
            domain.push(['amount_residual', '<', 0]);
        } else if (amount > 0) {
            domain.push(['amount_residual', '>', 0]);
        }
        
        let partnerId = false;
        const partner = this.recordData.partner_id;
        if (Array.isArray(partner) && partner.length > 0) {
            partnerId = partner[0];
        } else if (typeof partner === 'object' && partner !== null) {
            partnerId = partner.id || false;
        } else if (typeof partner === 'number') {
            partnerId = partner;
        }
        
        const resId = this.record?.resId;
        if (!resId) return;

        this.env.services.dialog.add(SelectCreateDialog, {
            resModel: "account.move.line",
            title: "Search: Journal Items to Match",
            domain: domain,
            context: {
                hudson_match_amount: amount,
                hudson_match_partner_id: partnerId || false,
            },
            multiSelect: true,
            noCreate: true,
            onSelected: async (resIds) => {
                if (resIds.length > 0) {
                    await this.orm.call(
                        "account.bank.statement.line",
                        "action_hudson_reconcile_items",
                        [[resId], resIds]
                    );
                    window.location.reload();
                }
            }
        });
    }

    async onUploadBills() {
        const resId = this.record?.resId;
        if (!resId) return;
        const action = await this.orm.call(
            "account.bank.statement.line",
            "action_hudson_upload_bills",
            [[resId]]
        );
        if (action) {
            this.action.doAction(action);
        }
    }

    async onDelete() {
        const resId = this.record?.resId;
        if (!resId) return;
        await this.orm.unlink("account.bank.statement.line", [resId]);
        if (this.record?.model?.load) {
            this.record.model.load();
        } else {
            window.location.reload();
        }
    }
    
    async onInternalTransfers() {
        const resId = this.record?.resId;
        if (!resId) return;
        await this.orm.call(
            "account.bank.statement.line",
            "action_hudson_internal_transfer",
            [[resId]]
        );
        window.location.reload();
    }
    
    async onManageModels() {
        this.env.services.action.doAction("account.action_account_reconcile_model");
    }
}

BankRecActionDropdown.template = "hudson_accounting_enhancements.BankRecActionDropdown";
BankRecActionDropdown.components = { Dropdown, DropdownItem };

export const bankRecActionDropdown = {
    component: BankRecActionDropdown,
};

registry.category("fields").add("bank_rec_action_dropdown", bankRecActionDropdown);

function hudsonSetPartnerAction(env, action) {
    env.services.dialog.add(SelectCreateDialog, {
        resModel: "res.partner",
        title: "Search: Partner",
        onSelected: async (resIds) => {
            if (resIds.length > 0) {
                const partnerId = resIds[0];
                const statementLineId = action.context.default_statement_line_id;
                await env.services.orm.write("account.bank.statement.line", [statementLineId], {
                    partner_id: partnerId
                });
                // Reload window to reflect changes
                window.location.reload();
            }
        }
    });
}
registry.category("actions").add("hudson_set_partner", hudsonSetPartnerAction);

function hudsonSetAccountAction(env, action) {
    env.services.dialog.add(SelectCreateDialog, {
        resModel: "account.account",
        title: "Search: Account",
        onSelected: async (resIds) => {
            if (resIds.length > 0) {
                const accountId = resIds[0];
                const statementLineId = action.context.default_statement_line_id;
                await env.services.orm.write("account.bank.statement.line", [statementLineId], {
                    hudson_account_id: accountId
                });
                window.location.reload();
            }
        }
    });
}
registry.category("actions").add("hudson_set_account", hudsonSetAccountAction);
