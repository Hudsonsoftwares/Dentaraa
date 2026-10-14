/** @odoo-module **/

import { Component, proxy, onWillStart, onWillUnmount, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";

export class DynamicReport extends Component {
    props = useProps(standardActionServiceProps);

    get reportParams() {
        return this._currentParams || this.props?.action?.params || {};
    }

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = proxy({
            title: "Loading...",
            columns: [],
            lines: [],
            expandedLines: {},
            currencyId: null,
            alert_message: null,
            filterSummary: {
                date: 'Fiscal Year',
                target_move: 'Posted Entries',
                account_type: 'receivable',
                date_basis: 'date_maturity',
                period_length: 30,
                show_draft: false,
                show_currency: false,
                show_account: false,
                hide_lines_at_0: false,
                split_horizontally: false,
                analytic_simulations: false,
                subtotals: false,
                partners: [],
                tags: [],
                gaap: 'Local Gaap',
                gaap_options: {
                    local_gaap: true
                }
            },
            available_ledgers: [],
            customDateFrom: '',
            customDateTo: '',
            partnerSearch: '',
            tagSearch: '',
            analyticSearch: '',
            analyticPlanSearch: '',
            partnerResults: [],
            tagResults: [],
            analyticResults: [],
            analyticPlanResults: [],
            unfoldAll: false,
            model_name: null,
            openDropdownLineId: null,
            dropdownIsDropup: false,
            searchQuery: '',
            selectedSplitLineId: null,
            splitSearchQuery: '',
            currency_symbol: '₹',
            integrations: { dms: false, knowledge: false },
        });

        // Stack of saved param objects for in-place sub-report navigation
        this._paramStack = [];
        // Active params (single source of truth — avoids OWL read-only props mutation)
        this._currentParams = null;

        this.handleClickOutside = (ev) => {
            if (this.state.openDropdownLineId) {
                if (!ev.target.closest('.o_dynamic_report_dropdown')) {
                    this.state.openDropdownLineId = null;
                }
            }
        };
        document.addEventListener('click', this.handleClickOutside);

        onWillStart(async () => {
            await this.fetchData();
        });

        onWillUnmount(() => {
            document.removeEventListener('click', this.handleClickOutside);
        });
    }

    toggleLineDropdown(lineId, ev = null) {
        if (this.state.openDropdownLineId === lineId) {
            this.state.openDropdownLineId = null;
            return;
        }
        this.state.openDropdownLineId = lineId;
        if (ev && ev.target) {
            const rect = ev.target.getBoundingClientRect();
            const spaceBelow = window.innerHeight - rect.bottom;
            this.state.dropdownIsDropup = (spaceBelow < 200);
        } else {
            this.state.dropdownIsDropup = false;
        }
    }

    formatDateDisplay(dateStr) {
        if (!dateStr) {
            const today = new Date();
            const d = String(today.getDate()).padStart(2, '0');
            const m = String(today.getMonth() + 1).padStart(2, '0');
            const y = today.getFullYear();
            return `${d}/${m}/${y}`;
        }
        if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
            const parts = dateStr.split('-');
            return `${parts[2]}/${parts[1]}/${parts[0]}`;
        }
        return dateStr;
    }

    isNegativeValue(val) {
        if (val === null || val === undefined || val === '') return false;
        if (typeof val === 'number') return val < -0.00001;
        const clean = String(val).replace(/[^0-9.-]/g, '');
        const num = parseFloat(clean);
        return !isNaN(num) && num < -0.00001;
    }

    isZeroValue(val) {
        if (val === null || val === undefined || val === '') return true;
        if (typeof val === 'number') return Math.abs(val) < 0.00001;
        const clean = String(val).replace(/[^0-9.-]/g, '');
        const num = parseFloat(clean);
        return isNaN(num) || Math.abs(num) < 0.00001;
    }

    async fetchData() {
        const action = this.props?.action || {};
        // Use _currentParams if set (in-place navigation), otherwise fall back to props
        let params = this.reportParams;
        let model_name = params.model_name || this.state.model_name || null;

        // Primary storage key is based on model_name; secondary/fallback key is the action ID.
        // We always write to BOTH keys so that back-navigation (where model_name may be missing
        // from the restored props) can still find the full params via the action ID.
        const actionId = action.id || action.tag || this.props?.actionId || 'default';
        const actionStorageKey = 'hudson_report_params_action_' + actionId;

        if (params.model_name) {
            // Params are fully specified — persist them under both keys
            const modelStorageKey = 'hudson_report_params_' + params.model_name;
            sessionStorage.setItem(modelStorageKey, JSON.stringify(params));
            sessionStorage.setItem(actionStorageKey, JSON.stringify(params));
            this._currentParams = params;
        } else {
            // Try to recover params: first from action-ID key (works after back-navigation),
            // then from model-name key if model_name is already known in state.
            let saved = sessionStorage.getItem(actionStorageKey);
            if (!saved && model_name) {
                saved = sessionStorage.getItem('hudson_report_params_' + model_name);
            }
            if (saved) {
                params = JSON.parse(saved);
                model_name = params.model_name || model_name;
                this._currentParams = params;
            }
        }
        
        const wizard_id = params.wizard_id || null;
        const data = params.data || {};
        
        this.state.model_name = model_name;
        
        if (!data.form) data.form = {};
        if (!data.form.date_from && !data.form.date_to && model_name !== 'account.aged.report') {
            const now = new Date();
            if (['account.deferred.revenue.report', 'account.deferred.expense.report'].includes(model_name)) {
                const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
                const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);
                data.form.date_from = firstDay.toISOString().split('T')[0];
                data.form.date_to = lastDay.toISOString().split('T')[0];
                const monthName = now.toLocaleString('default', { month: 'short' });
                this.state.filterSummary.date = `${monthName} ${now.getFullYear()}`;
            } else {
                const firstDay = new Date(now.getFullYear(), 0, 1);
                const lastDay = new Date(now.getFullYear(), 11, 31);
                data.form.date_from = firstDay.toISOString().split('T')[0];
                data.form.date_to = lastDay.toISOString().split('T')[0];
            }
            if (data.form.used_context) {
                data.form.used_context.date_from = data.form.date_from;
                data.form.used_context.date_to = data.form.date_to;
            }
        }

        // If it's an aged report, try to read the wizard's actual values to populate filterSummary
        if (model_name === 'account.aged.report') {
            const formData = data.form || data;
            if (formData.as_of_date || formData.date_to) {
                this.state.filterSummary.date = formData.as_of_date || formData.date_to;
            }
            if (formData.account_type) {
                this.state.filterSummary.account_type = formData.account_type;
            }
            if (formData.date_basis) {
                this.state.filterSummary.date_basis = formData.date_basis;
            }
            if (formData.period_length) {
                this.state.filterSummary.period_length = formData.period_length;
            }
            
            if (wizard_id) {
                try {
                    const wizData = await this.orm.read(model_name, [wizard_id], ['as_of_date', 'account_type', 'date_basis', 'period_length', 'show_draft', 'show_currency', 'show_account', 'hide_lines_at_0', 'partner_ids', 'partner_category_ids']);
                    if (wizData && wizData.length > 0) {
                        const wiz = wizData[0];
                        if (wiz.as_of_date) this.state.filterSummary.date = wiz.as_of_date;
                        if (wiz.account_type) this.state.filterSummary.account_type = wiz.account_type;
                        if (wiz.date_basis) this.state.filterSummary.date_basis = wiz.date_basis;
                        if (wiz.period_length) this.state.filterSummary.period_length = wiz.period_length;
                        this.state.filterSummary.show_draft = wiz.show_draft;
                        this.state.filterSummary.show_currency = wiz.show_currency;
                        this.state.filterSummary.show_account = wiz.show_account;
                        this.state.filterSummary.hide_lines_at_0 = wiz.hide_lines_at_0;
                        
                        if (wiz.partner_ids && wiz.partner_ids.length > 0) {
                            const partners = await this.orm.read('res.partner', wiz.partner_ids, ['id', 'name']);
                            this.state.filterSummary.partners = partners;
                        }
                        if (wiz.partner_category_ids && wiz.partner_category_ids.length > 0) {
                            const tags = await this.orm.read('res.partner.category', wiz.partner_category_ids, ['id', 'name']);
                            this.state.filterSummary.tags = tags;
                        }
                    }
                } catch (e) {
                    console.warn("Could not read wizard data", e);
                }
            }
        }

        const result = await this.orm.call("hudson.dynamic.report", "get_report_data", [
            model_name,
            wizard_id,
            data
        ]);

        try {
            const integrations = await this.orm.call("hudson.dynamic.report", "get_installed_integrations", []);
            this.state.integrations = integrations;
        } catch (e) {
            console.warn("Could not fetch integrations", e);
        }

        this.state.title = result.title;
        this.state.columns = result.columns;
        this.state.column_groups = result.column_groups || [];
        this.state.lines = result.lines;
        this.state.currencyId = result.currency_id;
        this.state.currency_symbol = result.currency_symbol || '₹';
        this.state.alert_message = result.alert_message || null;
        this.state.companies_description = result.companies_description || '';
        this.state.available_ledgers = result.available_ledgers || [];
        
        // Setup smart line expansion matching standard ERP reporting
        this.state.expandedLines = {};
        if (model_name === 'account.aged.report' || model_name === 'account.print.journal' || model_name === 'account.report.partner.ledger') {
            // In Aged reports, Journal Audit and Partner Ledger, groups/partners are collapsed by default unless Unfold All is active
            if (this.state.unfoldAll) {
                for (const line of result.lines) {
                    this.state.expandedLines[line.id] = true;
                }
            }
        } else if (model_name === 'account.cash.flow.wizard') {
            // In Cash Flow Statement, expand Level 1 & 2 by default so sections & sub-lines are visible, while accounts & transactions (Level 3+) stay collapsed
            for (const line of result.lines) {
                if (this.state.unfoldAll || line.level <= 2) {
                    this.state.expandedLines[line.id] = true;
                }
            }
        } else if (model_name === 'account.report.general.ledger') {
            // In General Ledger, expand Level 1 (Groups) and Level 2 (Accounts) so account headers & transactions are visible
            for (const line of result.lines) {
                if (line.level === 1 || line.level === 2) {
                    this.state.expandedLines[line.id] = true;
                }
            }
        } else if (model_name === 'account.balance.report') {
            // In Trial Balance, expand Level 1 (Groups) so all accounts are visible
            for (const line of result.lines) {
                if (line.level === 1) {
                    this.state.expandedLines[line.id] = true;
                }
            }
        } else {
            for (const line of result.lines) {
                this.state.expandedLines[line.id] = true;
            }
        }
    }

    async onDateFilter(type) {
        const data = this.reportParams.data || {};
        const form_data = data.form || data;
        const now = new Date();
        
        if (type === 'today') {
            const today = now.toISOString().split('T')[0];
            form_data.date_from = today;
            form_data.date_to = today;
            this.state.filterSummary.date = 'Today';
            this.state.filterSummary.date_type = 'today';
        } else if (type === 'this_month') {
            const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
            const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);
            form_data.date_from = firstDay.toISOString().split('T')[0];
            form_data.date_to = lastDay.toISOString().split('T')[0];
            this.state.filterSummary.date = 'This Month';
            this.state.filterSummary.date_type = 'this_month';
        } else if (type === 'this_quarter') {
            const quarter = Math.floor(now.getMonth() / 3);
            const firstDay = new Date(now.getFullYear(), quarter * 3, 1);
            const lastDay = new Date(now.getFullYear(), quarter * 3 + 3, 0);
            form_data.date_from = firstDay.toISOString().split('T')[0];
            form_data.date_to = lastDay.toISOString().split('T')[0];
            this.state.filterSummary.date = 'This Quarter';
            this.state.filterSummary.date_type = 'this_quarter';
        } else if (type === 'this_year') {
            // Assuming Jan-Dec fiscal year for simplicity
            const firstDay = new Date(now.getFullYear(), 0, 1);
            const lastDay = new Date(now.getFullYear(), 11, 31);
            form_data.date_from = firstDay.toISOString().split('T')[0];
            form_data.date_to = lastDay.toISOString().split('T')[0];
            this.state.filterSummary.date = 'Fiscal Year';
            this.state.filterSummary.date_type = 'this_year';
        }
        
        if (form_data.used_context) {
            form_data.used_context.date_from = form_data.date_from;
            form_data.used_context.date_to = form_data.date_to;
        }
        
        // Write to wizard to ensure backend sync
        const wizard_id = this.reportParams.wizard_id;
        const model_name = this.reportParams.model_name;
        if (wizard_id && model_name) {
            try {
                await this.orm.write(model_name, [wizard_id], {
                    date_from: form_data.date_from,
                    date_to: form_data.date_to,
                });
            } catch (e) {
                // Ignore field errors if model doesn't support date_from
                console.warn("Could not write date fields to wizard", e);
            }
        }
        
        await this.fetchData();
    }

    async applyCustomDates() {
        if (!this.state.customDateFrom || !this.state.customDateTo) return;
        
        const data = this.reportParams.data || {};
        const form_data = data.form || data;
        
        form_data.date_from = this.state.customDateFrom;
        form_data.date_to = this.state.customDateTo;
        this.state.filterSummary.date = `${this.state.customDateFrom} to ${this.state.customDateTo}`;
        
        if (form_data.used_context) {
            form_data.used_context.date_from = form_data.date_from;
            form_data.used_context.date_to = form_data.date_to;
        }
        
        const wizard_id = this.reportParams.wizard_id;
        const model_name = this.reportParams.model_name;
        if (wizard_id && model_name) {
            try {
                await this.orm.write(model_name, [wizard_id], {
                    date_from: form_data.date_from,
                    date_to: form_data.date_to,
                });
            } catch (e) {
                console.warn("Could not write date fields to wizard", e);
            }
        }
        
        await this.fetchData();
    }

    async onTargetMove(type) {
        const data = this.reportParams.data || {};
        const form_data = data.form || data;
        
        form_data.target_move = type;
        this.state.filterSummary.target_move = type === 'posted' ? 'Posted Entries' : 'All Entries';
        
        const wizard_id = this.reportParams.wizard_id;
        const model_name = this.reportParams.model_name;
        if (wizard_id && model_name) {
            await this.orm.write(model_name, [wizard_id], {
                target_move: form_data.target_move,
            });
        }
        
        await this.fetchData();
    }

    async onComparisonFilter(type) {
        this.state.filterSummary.comparison = type;
        const data = this.reportParams.data || {};
        const form_data = data.form || data;
        form_data.comparison = type;
        form_data.previous_periods = this.state.filterSummary.previous_periods || 1;
        if (type === 'specific_date') {
            form_data.date_to_cmp = this.state.filterSummary.date_to_cmp;
        }
        
        const wizard_id = this.reportParams.wizard_id;
        const model_name = this.reportParams.model_name;
        if (wizard_id && model_name) {
            try {
                // If model supports these fields
                await this.orm.write(model_name, [wizard_id], {
                    comparison: form_data.comparison,
                    previous_periods: form_data.previous_periods,
                    date_to_cmp: form_data.date_to_cmp || false
                });
            } catch (e) { }
        }
        await this.fetchData();
    }

    async onRounding(type) {
        this.state.filterSummary.rounding = type;
        const data = this.reportParams.data || {};
        const form_data = data.form || data;
        form_data.rounding = type;
        await this.fetchData();
    }

    closeBanner() {
        this.state.bannerClosed = true;
    }

    async onAgedDateFilter(type) {
        let newDate = '';
        const today = new Date();
        
        if (type === 'today') {
            newDate = today.toISOString().split('T')[0];
        } else if (type === 'end_last_month') {
            const date = new Date(today.getFullYear(), today.getMonth(), 0);
            newDate = date.toISOString().split('T')[0];
        } else if (type === 'end_last_quarter') {
            const q = Math.floor(today.getMonth() / 3);
            const date = new Date(today.getFullYear(), q * 3, 0);
            newDate = date.toISOString().split('T')[0];
        } else if (type === 'end_last_year') {
            const date = new Date(today.getFullYear(), 0, 0);
            newDate = date.toISOString().split('T')[0];
        } else if (type === 'custom') {
            newDate = this.state.customDateFrom;
            if (!newDate) return;
        }

        this.state.filterSummary.date = newDate;
        const data = this.reportParams.data || {};
        const form_data = data.form || data;
        form_data.as_of_date = newDate;
        form_data.date_to = newDate;

        const wizard_id = this.reportParams.wizard_id;
        const model_name = this.reportParams.model_name;
        if (wizard_id && model_name === 'account.aged.report') {
            try {
                await this.orm.write(model_name, [wizard_id], { as_of_date: newDate });
            } catch (e) {}
        }
        await this.fetchData();
    }

    async onAgedAccountFilter(type) {
        this.state.filterSummary.account_type = type;
        const data = this.reportParams.data || {};
        const form_data = data.form || data;
        form_data.account_type = type;

        const wizard_id = this.reportParams.wizard_id;
        const model_name = this.reportParams.model_name;
        if (wizard_id && model_name === 'account.aged.report') {
            try {
                await this.orm.write(model_name, [wizard_id], { account_type: type });
            } catch (e) {}
        }
        await this.fetchData();
    }

    async onAgedBasisFilter(type) {
        this.state.filterSummary.date_basis = type;
        const data = this.reportParams.data || {};
        const form_data = data.form || data;
        form_data.date_basis = type;

        const wizard_id = this.reportParams.wizard_id;
        const model_name = this.reportParams.model_name;
        if (wizard_id && model_name === 'account.aged.report') {
            try {
                await this.orm.write(model_name, [wizard_id], { date_basis: type });
            } catch (e) {}
        }
        await this.fetchData();
    }

    async onAgedPeriodFilter(days) {
        const p = parseInt(days);
        this.state.filterSummary.period_length = p;
        const data = this.reportParams.data || {};
        const form_data = data.form || data;
        form_data.period_length = p;

        const wizard_id = this.reportParams.wizard_id;
        const model_name = this.reportParams.model_name;
        if (wizard_id && model_name === 'account.aged.report') {
            try {
                await this.orm.write(model_name, [wizard_id], { period_length: p });
            } catch (e) {}
        }
        await this.fetchData();
    }

    async onAgedToggleOption(option) {
        this.state.filterSummary[option] = !this.state.filterSummary[option];
        const wizard_id = this.reportParams.wizard_id;
        const model_name = this.reportParams.model_name;
        if (wizard_id && model_name === 'account.aged.report') {
            const vals = {};
            vals[option] = this.state.filterSummary[option];
            await this.orm.write(model_name, [wizard_id], vals);
        }
        await this.fetchData();
    }

    onUnfoldAllToggle() {
        this.state.unfoldAll = !this.state.unfoldAll;
        const newExpanded = {};
        const model_name = this.state.model_name;
        if (this.state.unfoldAll) {
            this.state.lines.forEach(l => {
                newExpanded[l.id] = true;
            });
        } else if (model_name === 'account.cash.flow.wizard') {
            this.state.lines.forEach(l => {
                if (l.level <= 2) {
                    newExpanded[l.id] = true;
                }
            });
        }
        this.state.expandedLines = newExpanded;
    }

    async onPartnerSearch(ev) {
        const val = ev.target.value;
        if (!val) {
            await this.loadDefaultPartners();
            return;
        }
        if (val.length < 2) {
            this.state.partnerResults = [];
            return;
        }
        // Basic debounce
        if (this.partnerTimeout) clearTimeout(this.partnerTimeout);
        this.partnerTimeout = setTimeout(async () => {
            const results = await this.orm.searchRead('res.partner', [['name', 'ilike', val]], ['id', 'name'], { limit: 10 });
            this.state.partnerResults = results;
        }, 300);
    }

    async loadDefaultPartners() {
        if (!this.state.partnerResults || this.state.partnerResults.length === 0) {
            const results = await this.orm.searchRead('res.partner', [], ['id', 'name'], { limit: 20, order: 'name asc' });
            this.state.partnerResults = results;
        }
    }

    async onTagSearch(ev) {
        const val = ev.target.value;
        if (!val || val.length < 2) {
            this.state.tagResults = [];
            return;
        }
        if (this.tagTimeout) clearTimeout(this.tagTimeout);
        this.tagTimeout = setTimeout(async () => {
            const results = await this.orm.searchRead('res.partner.category', [['name', 'ilike', val]], ['id', 'name'], { limit: 10 });
            this.state.tagResults = results;
        }, 300);
    }

    selectPartner(p) {
        if (!this.state.filterSummary.partners.find(x => x.id === p.id)) {
            this.state.filterSummary.partners.push(p);
        }
        this.state.partnerSearch = '';
        this.state.partnerResults = [];
    }

    selectTag(t) {
        if (!this.state.filterSummary.tags.find(x => x.id === t.id)) {
            this.state.filterSummary.tags.push(t);
        }
        this.state.tagSearch = '';
        this.state.tagResults = [];
    }

    removePartner(pid) {
        this.state.filterSummary.partners = this.state.filterSummary.partners.filter(p => p.id !== pid);
    }

    removeTag(tid) {
        this.state.filterSummary.tags = this.state.filterSummary.tags.filter(t => t.id !== tid);
    }

    async applyPartnerFilters() {
        const wizard_id = this.reportParams.wizard_id;
        const model_name = this.reportParams.model_name;
        if (wizard_id && model_name) {
            try {
                await this.orm.write(model_name, [wizard_id], { 
                    partner_ids: [[6, 0, this.state.filterSummary.partners.map(p => p.id)]],
                    partner_category_ids: [[6, 0, this.state.filterSummary.tags.map(t => t.id)]]
                });
            } catch (e) { }
        }
        const data = this.reportParams.data || {};
        const form_data = data.form || data;
        form_data.partner_ids = this.state.filterSummary.partners.map(p => p.id);
        form_data.partner_category_ids = this.state.filterSummary.tags.map(t => t.id);
        await this.fetchData();
    }

    async onAnalyticSearch(ev) {
        const val = ev.target.value;
        if (!val) {
            await this.loadDefaultAnalytics();
            return;
        }
        if (val.length < 2) {
            this.state.analyticResults = [];
            return;
        }
        if (this.analyticTimeout) clearTimeout(this.analyticTimeout);
        this.analyticTimeout = setTimeout(async () => {
            const results = await this.orm.searchRead('account.analytic.account', [['name', 'ilike', val]], ['id', 'name'], { limit: 10 });
            this.state.analyticResults = results;
        }, 300);
    }

    async loadDefaultAnalytics() {
        if (!this.state.analyticResults || this.state.analyticResults.length === 0) {
            const results = await this.orm.searchRead('account.analytic.account', [], ['id', 'name'], { limit: 20, order: 'name asc' });
            this.state.analyticResults = results;
        }
    }

    selectAnalyticAccount(a) {
        if (!this.state.filterSummary.analytic_accounts) this.state.filterSummary.analytic_accounts = [];
        if (!this.state.filterSummary.analytic_accounts.find(x => x.id === a.id)) {
            this.state.filterSummary.analytic_accounts.push(a);
        }
        this.state.analyticSearch = '';
        this.state.analyticResults = [];
    }

    removeAnalyticAccount(aid) {
        if (this.state.filterSummary.analytic_accounts) {
            this.state.filterSummary.analytic_accounts = this.state.filterSummary.analytic_accounts.filter(a => a.id !== aid);
        }
    }

    async applyAnalyticFilters() {
        const wizard_id = this.reportParams.wizard_id;
        const model_name = this.reportParams.model_name;
        if (wizard_id && model_name) {
            try {
                await this.orm.write(model_name, [wizard_id], { 
                    analytic_account_ids: [[6, 0, (this.state.filterSummary.analytic_accounts || []).map(a => a.id)]]
                });
            } catch (e) { }
        }
        const data = this.reportParams.data || {};
        const form_data = data.form || data;
        form_data.analytic_account_ids = (this.state.filterSummary.analytic_accounts || []).map(a => a.id);
        form_data.analytic_plan_ids = (this.state.filterSummary.analytic_plans || []).map(p => p.id);
        await this.fetchData();
    }

    async onAnalyticPlanSearch(ev) {
        const val = ev.target.value;
        if (!val) {
            await this.loadDefaultAnalyticPlans();
            return;
        }
        if (val.length < 2) {
            this.state.analyticPlanResults = [];
            return;
        }
        if (this.analyticPlanTimeout) clearTimeout(this.analyticPlanTimeout);
        this.analyticPlanTimeout = setTimeout(async () => {
            const results = await this.orm.searchRead('account.analytic.plan', [['name', 'ilike', val]], ['id', 'name'], { limit: 10 });
            this.state.analyticPlanResults = results;
        }, 300);
    }

    async loadDefaultAnalyticPlans() {
        if (!this.state.analyticPlanResults || this.state.analyticPlanResults.length === 0) {
            const results = await this.orm.searchRead('account.analytic.plan', [], ['id', 'name'], { limit: 20, order: 'name asc' });
            this.state.analyticPlanResults = results;
        }
    }

    selectAnalyticPlan(p) {
        if (!this.state.filterSummary.analytic_plans) this.state.filterSummary.analytic_plans = [];
        if (!this.state.filterSummary.analytic_plans.find(x => x.id === p.id)) {
            this.state.filterSummary.analytic_plans.push(p);
        }
        this.state.analyticPlanSearch = '';
        this.state.analyticPlanResults = [];
    }

    removeAnalyticPlan(pid) {
        if (this.state.filterSummary.analytic_plans) {
            this.state.filterSummary.analytic_plans = this.state.filterSummary.analytic_plans.filter(p => p.id !== pid);
        }
    }

    onSearchInput(ev) {
        this.state.searchQuery = ev.target.value;
    }

    getGaapButtonLabel() {
        const gaap = this.state.filterSummary.gaap_options || { local_gaap: true };
        let selectedCount = 0;
        let lastName = '';
        
        if (gaap.local_gaap) {
            selectedCount++;
            lastName = 'Local Gaap';
        }
        
        if (this.state.available_ledgers) {
            for (const ledger of this.state.available_ledgers) {
                if (gaap[ledger.id]) {
                    selectedCount++;
                    lastName = ledger.name;
                }
            }
        }
        
        if (selectedCount === 0) return 'All Ledgers';
        if (selectedCount === 1) return lastName;
        return 'Multiple Ledgers';
    }

    async toggleGaap(option) {
        if (!this.state.filterSummary.gaap_options) {
            this.state.filterSummary.gaap_options = { local_gaap: true };
        }
        if (option === 'local_gaap') {
            this.state.filterSummary.gaap_options = { local_gaap: true };
            if (this.state.available_ledgers) {
                for (const ledger of this.state.available_ledgers) {
                    this.state.filterSummary.gaap_options[ledger.id] = false;
                }
            }
        } else {
            this.state.filterSummary.gaap_options[option] = !this.state.filterSummary.gaap_options[option];
            if (this.state.filterSummary.gaap_options[option]) {
                this.state.filterSummary.gaap_options.local_gaap = false;
            }
            let anySelected = false;
            if (this.state.available_ledgers) {
                for (const ledger of this.state.available_ledgers) {
                    if (this.state.filterSummary.gaap_options[ledger.id]) anySelected = true;
                }
            }
            if (!anySelected) {
                this.state.filterSummary.gaap_options.local_gaap = true;
            }
        }
        
        this.state.filterSummary.gaap = this.getGaapButtonLabel();
        
        const data = this.reportParams.data || {};
        const form_data = data.form || data;
        form_data.gaap_options = this.state.filterSummary.gaap_options;
        
        await this.fetchData();
    }

    onGaapFilter(type) {
        this.state.filterSummary.gaap = type;
    }

    async onPartnerAccountFilter(type) {
        this.state.filterSummary.account_type = type;
        const data = this.reportParams.data || {};
        const form_data = data.form || data;
        form_data.account_type = type;
        await this.fetchData();
    }

    async switchReport(newModelName) {
        if (this.state.model_name === newModelName) return;
        this.state.model_name = newModelName;
        if (!this._currentParams) {
            this._currentParams = Object.assign({}, this.reportParams);
        }
        this._currentParams.model_name = newModelName;
        this._currentParams.wizard_id = null;
        if (this.props?.action?.params) {
            this.props.action.params.model_name = newModelName;
            this.props.action.params.wizard_id = null;
        }
        await this.fetchData();
    }

    toggleHideLinesAt0() {
        this.state.filterSummary.hide_lines_at_0 = !this.state.filterSummary.hide_lines_at_0;
    }

    toggleSplitHorizontally() {
        this.state.filterSummary.split_horizontally = !this.state.filterSummary.split_horizontally;
    }

    async toggleDraftEntries() {
        const isDraft = this.state.filterSummary.target_move === 'All Entries';
        await this.onTargetMove(isDraft ? 'posted' : 'all');
    }

    toggleAnalyticSimulations() {
        this.state.filterSummary.analytic_simulations = !this.state.filterSummary.analytic_simulations;
    }

    toggleSubtotals() {
        this.state.filterSummary.subtotals = !this.state.filterSummary.subtotals;
    }

    isLineZero(line) {
        const checkFields = ['balance', 'debit', 'credit', 'tax', 'net', 'total', 'p0', 'p1', 'p2', 'p3', 'p4', 'not_due', 'amount_currency'];
        for (const f of checkFields) {
            if (line[f] !== undefined && line[f] !== null && Math.abs(Number(line[f])) > 0.0001) {
                return false;
            }
        }
        for (let i = 1; i <= 10; i++) {
            if (line[`balance_cmp_${i}`] !== undefined && Math.abs(Number(line[`balance_cmp_${i}`])) > 0.0001) {
                return false;
            }
        }
        return true;
    }

    hasNonZeroChildren(line) {
        const lines = this.state.lines;
        const index = lines.indexOf(line);
        if (index === -1) return false;
        for (let i = index + 1; i < lines.length; i++) {
            if (lines[i].level <= line.level) break;
            if (!this.isLineZero(lines[i])) return true;
        }
        return false;
    }

    isSplitHorizontally() {
        return !!this.state.filterSummary.split_horizontally;
    }

    getLeftSplitLines() {
        if (!this.state.lines || !this.state.lines.length) return [];
        const lines = this.state.lines;

        // 1. Balance sheet: Assets on Left
        const titleUpper = (this.state.title || '').toUpperCase();
        if (titleUpper.includes('BALANCE SHEET') || lines.some(l => (l.name || '').toUpperCase().includes('ASSET') && l.level === 1)) {
            let left = [];
            let inLeft = false;
            for (let i = 0; i < lines.length; i++) {
                const l = lines[i];
                const nameUpper = (l.name || '').toUpperCase().trim();
                if (l.level === 1 || l.is_summary_total) {
                    if (nameUpper.includes('ASSET') && !nameUpper.includes('LIABILIT') && !nameUpper.includes('EQUITY')) {
                        inLeft = true;
                        left.push(l);
                    } else if (nameUpper.includes('LIABILIT') || nameUpper.includes('EQUITY') || nameUpper.includes('PASSIV') || nameUpper.includes('CAPITAL')) {
                        inLeft = false;
                    } else if (inLeft) {
                        left.push(l);
                    }
                } else if (inLeft) {
                    left.push(l);
                }
            }
            if (left.length > 0) return left;
        }

        // 2. All other reports (General Ledger, Trial Balance, Partner Ledger, Profit & Loss, Cash Flow, Tax, Aged, etc.):
        // Group into complete hierarchical blocks starting at the minimum level (e.g. Level 1 parent groups/accounts)
        const nonSummary = lines.filter(l => !l.is_summary_total);
        const minLevel = nonSummary.length ? Math.min(...nonSummary.map(l => l.level || 1)) : 1;

        const blocks = [];
        let currentBlock = [];
        for (let i = 0; i < lines.length; i++) {
            const l = lines[i];
            if (l.level === minLevel && currentBlock.length > 0) {
                blocks.push(currentBlock);
                currentBlock = [];
            }
            currentBlock.push(l);
        }
        if (currentBlock.length > 0) blocks.push(currentBlock);

        if (blocks.length > 1) {
            const mid = Math.ceil(blocks.length / 2);
            return blocks.slice(0, mid).flat();
        }

        // If only 1 root block exists, split at the direct children (minLevel + 1)
        if (blocks.length === 1 && lines.length > 1) {
            const root = lines[0];
            const subBlocks = [];
            let subCurrent = [];
            for (let i = 1; i < lines.length; i++) {
                const l = lines[i];
                if (l.level === minLevel + 1 && subCurrent.length > 0) {
                    subBlocks.push(subCurrent);
                    subCurrent = [];
                }
                subCurrent.push(l);
            }
            if (subCurrent.length > 0) subBlocks.push(subCurrent);
            if (subBlocks.length > 1) {
                const midSub = Math.ceil(subBlocks.length / 2);
                return [root, ...subBlocks.slice(0, midSub).flat()];
            }
        }

        const mid = Math.ceil(lines.length / 2);
        return lines.slice(0, mid);
    }

    getRightSplitLines() {
        if (!this.state.lines || !this.state.lines.length) return [];
        const lines = this.state.lines;

        // 1. Balance sheet: Liabilities & Equity on Right
        const titleUpper = (this.state.title || '').toUpperCase();
        if (titleUpper.includes('BALANCE SHEET') || lines.some(l => (l.name || '').toUpperCase().includes('LIABILIT') || (l.name || '').toUpperCase().includes('EQUITY'))) {
            let right = [];
            let inRight = false;
            for (let i = 0; i < lines.length; i++) {
                const l = lines[i];
                const nameUpper = (l.name || '').toUpperCase().trim();
                if (l.level === 1 || l.is_summary_total) {
                    if (nameUpper.includes('LIABILIT') || nameUpper.includes('EQUITY') || nameUpper.includes('PASSIV') || nameUpper.includes('CAPITAL')) {
                        inRight = true;
                        right.push(l);
                    } else if (nameUpper.includes('ASSET') && !nameUpper.includes('LIABILIT') && !nameUpper.includes('EQUITY')) {
                        inRight = false;
                    } else if (inRight) {
                        right.push(l);
                    }
                } else if (inRight) {
                    right.push(l);
                }
            }
            if (right.length > 0) return right;
        }

        // 2. All other reports:
        const nonSummary = lines.filter(l => !l.is_summary_total);
        const minLevel = nonSummary.length ? Math.min(...nonSummary.map(l => l.level || 1)) : 1;

        const blocks = [];
        let currentBlock = [];
        for (let i = 0; i < lines.length; i++) {
            const l = lines[i];
            if (l.level === minLevel && currentBlock.length > 0) {
                blocks.push(currentBlock);
                currentBlock = [];
            }
            currentBlock.push(l);
        }
        if (currentBlock.length > 0) blocks.push(currentBlock);

        if (blocks.length > 1) {
            const mid = Math.ceil(blocks.length / 2);
            return blocks.slice(mid).flat();
        }

        if (blocks.length === 1 && lines.length > 1) {
            const subBlocks = [];
            let subCurrent = [];
            for (let i = 1; i < lines.length; i++) {
                const l = lines[i];
                if (l.level === minLevel + 1 && subCurrent.length > 0) {
                    subBlocks.push(subCurrent);
                    subCurrent = [];
                }
                subCurrent.push(l);
            }
            if (subCurrent.length > 0) subBlocks.push(subCurrent);
            if (subBlocks.length > 1) {
                const midSub = Math.ceil(subBlocks.length / 2);
                return subBlocks.slice(midSub).flat();
            }
        }

        const mid = Math.ceil(lines.length / 2);
        return lines.slice(mid);
    }

    toggleExpand(lineId) {
        this.state.expandedLines[lineId] = !this.state.expandedLines[lineId];
    }

    isVisible(line) {
        if (this.state.filterSummary.hide_lines_at_0) {
            if (this.isLineZero(line) && !this.hasNonZeroChildren(line)) {
                return false;
            }
        }

        if (this.state.searchQuery) {
            const q = this.state.searchQuery.toLowerCase().trim();
            if (q) {
                const matches = (l) => {
                    for (const key of ['name', 'partner', 'account', 'journal', 'matching']) {
                        if (l[key] && String(l[key]).toLowerCase().includes(q)) return true;
                    }
                    return false;
                };
                
                if (matches(line)) return true;
                
                // If it's a parent line and has children matching, show parent
                const lines = this.state.lines;
                const index = lines.indexOf(line);
                for (let i = index + 1; i < lines.length; i++) {
                    if (lines[i].level <= line.level) break;
                    if (matches(lines[i])) return true;
                }
                return false;
            }
        }

        if (line.level === 1) return true;
        
        const lines = this.state.lines;
        const index = lines.indexOf(line);
        for (let i = index - 1; i >= 0; i--) {
            if (lines[i].level < line.level) {
                if (!this.state.expandedLines[lines[i].id]) {
                    return false;
                }
                if (!this.isVisible(lines[i])) {
                    return false;
                }
                break;
            }
        }
        return true;
    }

    getAgedAccountLabel() {
        const t = this.state.filterSummary.account_type;
        if (t === 'payable') return 'Account: Payable';
        if (t === 'receivable') return 'Account: Receivable';
        if (t === 'non_trade_payable') return 'Account: Non-Trade Payable';
        if (t === 'non_trade_receivable') return 'Account: Non-Trade Receivable';
        return 'Account: ' + (t ? t.replace(/_/g, ' ') : 'Payable');
    }

    formatDateDisplay(dateStr) {
        if (!dateStr) {
            const now = new Date();
            const d = String(now.getDate()).padStart(2, '0');
            const m = String(now.getMonth() + 1).padStart(2, '0');
            const y = now.getFullYear();
            return `${d}/${m}/${y}`;
        }
        if (typeof dateStr === 'string' && dateStr.includes('-')) {
            const parts = dateStr.split('-');
            if (parts.length === 3) {
                return `${parts[2]}/${parts[1]}/${parts[0]}`;
            }
        }
        return dateStr;
    }

    isNegativeValue(val) {
        if (val === undefined || val === null || val === '') return false;
        return (Number(val) || 0) < -0.005;
    }

    isZeroValue(val) {
        if (val === undefined || val === null || val === '') return true;
        return Math.abs(Number(val) || 0) < 0.005;
    }

    getColumnClass(col) {
        if (!col) return '';
        if (col.type === 'monetary') return 'col-monetary';
        const field = (col.field || '').replace(/_/g, '-');
        return `col-${field}`;
    }

    getMonetaryValueClass(val) {
        if (this.isZeroValue(val)) return 'o_report_val_zero';
        if (this.isNegativeValue(val)) return 'o_report_val_negative';
        return 'o_report_val_positive';
    }

    formatMonetary(value, line, col) {
        if (value === undefined || value === null || value === '') return "";
        let num = Number(value);
        if (isNaN(num)) return value;
        const rounding = this.state.filterSummary.rounding !== undefined ? this.state.filterSummary.rounding : '.';
        if (rounding === 'K') {
            num = num / 1000;
        } else if (rounding === 'L') {
            num = num / 100000;
        } else if (rounding === 'M') {
            num = num / 1000000;
        }
        const decimals = (rounding === '.') ? 2 : 0;
        const formatted = num.toLocaleString('en-IN', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
        let symbol = this.state.currency_symbol || '₹';
        if (col && col.field === 'amount_currency' && line && line.foreign_currency_symbol) {
            symbol = line.foreign_currency_symbol;
        }
        return `${symbol} ${formatted}`;
    }

    async openExchangeRates() {
        await this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Exchange Rates',
            res_model: 'res.currency.rate',
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
        });
    }

    async createAdjustmentEntry() {
        const date = this.state.filterSummary.date || '';
        await this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Make Adjustment Entry',
            res_model: 'account.unrealized.currency.adjustment.wizard',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_date': (date && date !== 'Fiscal Year') ? date : undefined,
            }
        });
    }

    hasChildren(line) {
        const lines = this.state.lines;
        const index = lines.indexOf(line);
        if (index < lines.length - 1) {
            return lines[index + 1].level > line.level;
        }
        return false;
    }
    
    async onLineClicked(line) {
        const params = this.reportParams;
        const model_name = params.model_name;
        const data = params.data || {};
        const form_data = data.form || data;
        
        // Toggle expand for group lines when row is clicked
        if (line.type === 'group' && this.hasChildren(line)) {
            this.toggleExpand(line.id);
            return;
        }
        
        // 1. Click on a transaction / move line (in Cash Flow, General Ledger, Partner Ledger, Trial Balance)
        if (line.move_id || line.type === 'move_line' || line.move_line_id) {
            if (line.move_id) {
                let docTitle = 'Journal Entry';
                if (['out_invoice', 'out_refund', 'out_receipt'].includes(line.move_type)) {
                    docTitle = 'Customer Invoice';
                } else if (['in_invoice', 'in_refund', 'in_receipt'].includes(line.move_type)) {
                    docTitle = 'Vendor Bill';
                }
                
                await this.action.doAction({
                    type: 'ir.actions.act_window',
                    name: docTitle,
                    res_model: 'account.move',
                    res_id: line.move_id,
                    view_mode: 'form',
                    views: [[false, 'form']],
                });
                return;
            } else if (line.move_line_id) {
                await this.action.doAction({
                    type: 'ir.actions.act_window',
                    name: 'Journal Item',
                    res_model: 'account.move.line',
                    res_id: line.move_line_id,
                    view_mode: 'form',
                    views: [[false, 'form']],
                });
                return;
            }
        }
        
        // 2. Click on an Account line (Trial Balance, General Ledger, Cash Flow, Balance Sheet, P&L)
        if (line.type === 'account') {
            const date_from = form_data.date_from || form_data.date_from_cmp;
            const date_to = form_data.date_to || form_data.date_to_cmp;
            
            const domain = [];
            if (line.account_id) {
                domain.push(['account_id', '=', line.account_id]);
            } else if (line.name) {
                const code = line.name.split(' ')[0];
                domain.push(['account_id.code', '=', code]);
            }
            
            if (date_from) domain.push(['date', '>=', date_from]);
            if (date_to) domain.push(['date', '<=', date_to]);
            if (form_data.target_move === 'posted') domain.push(['move_id.state', '=', 'posted']);
            
            await this.action.doAction({
                type: 'ir.actions.act_window',
                name: `Journal Items - ${line.name}`,
                res_model: 'account.move.line',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: domain,
            });
        }
    }

    async onAuditTax(line) {
        if (!line.tax_id) return;
        
        const params = this.reportParams;
        const data = params.data || {};
        const form_data = data.form || data;
        
        const date_from = form_data.date_from;
        const date_to = form_data.date_to;
        
        const action = {
            type: 'ir.actions.act_window',
            name: 'Journal Items for Tax Audit',
            res_model: 'account.move.line',
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            domain: ['|', ['tax_line_id', '=', line.tax_id], ['tax_ids', 'in', [line.tax_id]]],
            context: {
                'search_default_group_by_account': 1,
            }
        };
        
        if (date_from) action.domain.push(['date', '>=', date_from]);
        if (date_to) action.domain.push(['date', '<=', date_to]);
        
        await this.action.doAction(action);
    }

    async onActionClicked(line, actionName) {
        const params = this.reportParams;
        const data = params.data || {};
        const form_data = data.form || data;
        
        if (actionName === 'open_partner' && line.partner_id) {
            await this.action.doAction({
                type: 'ir.actions.act_window',
                name: 'Partner',
                res_model: 'res.partner',
                res_id: line.partner_id,
                view_mode: 'form',
                views: [[false, 'form']],
            });
        } else if (actionName === 'open_journal_items') {
            const date_from = form_data.date_from;
            const date_to = form_data.date_to;
            
            const domain = [];
            if (line.account_id) {
                domain.push(['account_id', '=', line.account_id]);
            } else if (line.name && line.type === 'account') {
                const code = line.name.split(' ')[0];
                domain.push(['account_id.code', '=', code]);
            }
            if (line.partner_id) domain.push(['partner_id', '=', line.partner_id]);
            if (line.journal_id) domain.push(['journal_id', '=', line.journal_id]);
            if (date_from) domain.push(['date', '>=', date_from]);
            if (date_to) domain.push(['date', '<=', date_to]);
            if (form_data.target_move === 'posted') domain.push(['move_id.state', '=', 'posted']);
            
            const action = {
                type: 'ir.actions.act_window',
                name: `Journal Items - ${line.name}`,
                res_model: 'account.move.line',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: domain,
            };
            
            await this.action.doAction(action);
        } else if (actionName === 'open_general_ledger') {
            const date_from = form_data.date_from;
            const date_to = form_data.date_to;
            
            const domain = [];
            if (line.account_id) {
                domain.push(['account_id', '=', line.account_id]);
            } else if (line.name) {
                const code = line.name.split(' ')[0];
                domain.push(['account_id.code', '=', code]);
            }
            if (date_from) domain.push(['date', '>=', date_from]);
            if (date_to) domain.push(['date', '<=', date_to]);
            if (form_data.target_move === 'posted') domain.push(['move_id.state', '=', 'posted']);
            
            const action = {
                type: 'ir.actions.act_window',
                name: `General Ledger - ${line.name}`,
                res_model: 'account.move.line',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: domain,
                context: {
                    'search_default_group_by_account': 1,
                    'search_default_posted': form_data.target_move === 'posted' ? 1 : 0,
                },
            };
            
            await this.action.doAction(action);
        } else if (actionName === 'open_journal_entry' && line.move_id) {
            let docTitle = 'Journal Entry';
            if (['out_invoice', 'out_refund'].includes(line.move_type)) {
                docTitle = 'Customer Invoice';
            } else if (['in_invoice', 'in_refund'].includes(line.move_type)) {
                docTitle = 'Vendor Bill';
            }
            await this.action.doAction({
                type: 'ir.actions.act_window',
                name: docTitle,
                res_model: 'account.move',
                res_id: line.move_id,
                view_mode: 'form',
                views: [[false, 'form']],
            });
        } else if (actionName === 'open_statement' && line.partner_id) {
            const action = await this.orm.call("hudson.dynamic.report", "action_open_statement", [
                line.partner_id
            ]);
            if (action) {
                await this.action.doAction(action);
            }
        }
    }

    async exportPDF() {
        const params = this.reportParams;
        const model_name = params.model_name;
        const wizard_id = params.wizard_id;
        const data = params.data || {};
        
        if (model_name && wizard_id) {
            try {
                const context = {
                    active_model: data.model || this.props?.action?.context?.active_model || model_name,
                    active_ids: data.ids || this.props?.action?.context?.active_ids || [wizard_id],
                    active_id: (data.ids && data.ids[0]) || this.props?.action?.context?.active_id || wizard_id,
                };
                const action = await this.orm.call(model_name, "check_report", [[wizard_id]], { context });
                if (action) {
                    if (!action.context) {
                        action.context = {};
                    }
                    Object.assign(action.context, context);
                    await this.action.doAction(action);
                    return;
                }
            } catch (e) {
                console.warn("Could not execute check_report, falling back to window.print", e);
            }
        }
        window.print();
    }

    async onExportToDocuments() {
        const reportData = {
            title: this.state.title,
            columns: this.state.columns,
            lines: this.state.lines,
            date_str: this.state.filterSummary.date === 'Fiscal Year' ? new Date().toLocaleDateString() : this.state.filterSummary.date
        };
        const params = this.reportParams;
        const modelName = params.model_name || this.state.model_name;
        const wizardId = params.wizard_id || this.state.wizard_id;
        await this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Export to Documents',
            res_model: 'hudson.report.export.dms.wizard',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                default_name: this.state.title,
                default_report_data: JSON.stringify(reportData),
                default_model_name: modelName,
                default_wizard_id: wizardId,
            }
        });
    }

    async onInsertInArticle() {
        const reportData = {
            title: this.state.title,
            columns: this.state.columns,
            lines: this.state.lines,
            date_str: this.state.filterSummary.date === 'Fiscal Year' ? new Date().toLocaleDateString() : this.state.filterSummary.date
        };
        await this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Insert in Article',
            res_model: 'hudson.report.export.knowledge.wizard',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                default_name: this.state.title,
                default_report_data: JSON.stringify(reportData)
            }
        });
    }

    exportCSV() {
        const columns = this.state.columns || [];
        const lines = this.state.lines || [];
        
        // Build CSV header
        const headers = columns.map(c => `"${(c.label || '').replace(/"/g, '""')}"`);
        const rows = [headers.join(',')];
        
        for (const line of lines) {
            const row = columns.map(col => {
                let val = line[col.field];
                if (val === undefined || val === null) {
                    val = '';
                } else if (col.type === 'monetary') {
                    val = typeof val === 'number' ? val.toFixed(2) : String(val);
                } else {
                    val = String(val);
                }
                return `"${val.replace(/"/g, '""')}"`;
            });
            rows.push(row.join(','));
        }
        
        const csvContent = "\uFEFF" + rows.join('\r\n'); // Add UTF-8 BOM for Excel
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement("a");
        const url = URL.createObjectURL(blob);
        link.setAttribute("href", url);
        const filename = `${(this.state.title || 'report').replace(/[\s\/\\?%*:|"<>]/g, '_')}_${new Date().toISOString().split('T')[0]}.csv`;
        link.setAttribute("download", filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    exportXLSX() {
        // Export all lines regardless of expansion state
        const lines = this.state.lines;
        
        // Prepare data for backend
        const reportData = {
            title: this.state.title,
            columns: this.state.columns,
            lines: lines,
            date_str: this.state.filterSummary.date === 'Fiscal Year' ? new Date().toLocaleDateString() : this.state.filterSummary.date
        };
        
        // Create a hidden form to submit via POST for file download
        const form = document.createElement("form");
        form.method = "POST";
        form.action = "/hudson_dynamic_reports/export_xlsx";
        
        const dataInput = document.createElement("input");
        dataInput.type = "hidden";
        dataInput.name = "data";
        dataInput.value = JSON.stringify(reportData);
        form.appendChild(dataInput);
        
        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);
    }

    exportJSON() {
        const data = {
            title: this.state.title,
            columns: this.state.columns,
            lines: this.state.lines
        };
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const link = document.createElement("a");
        const url = URL.createObjectURL(blob);
        link.setAttribute("href", url);
        link.setAttribute("download", `${this.state.title.replace(/\s+/g, '_')}.json`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }
}

DynamicReport.template = "hudson_dynamic_reports.DynamicReport";

registry.category("actions").add("hudson_dynamic_reports.dynamic_report", DynamicReport);
registry.category("actions").add("hudson_accounting_enhancements.dynamic_report", DynamicReport);

