env = self.env
try:
    views = env['res.company'].get_views(views=[(False, 'form'), (False, 'list'), (False, 'search')])
    print('VIEWS LOADED SUCCESSFULLY')
except Exception as e:
    import traceback
    traceback.print_exc()
