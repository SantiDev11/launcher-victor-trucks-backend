content = open('backend/server.py', 'r', encoding='utf-8').read()
old = '''      existing = (
          supabase_admin
          .table("mod_access")
          .select("id")
          .eq("user_id", user_id)
          .eq("mod_id", req.mod_id)
          .maybe_single()
          .execute()
      )
      payload = {
          "user_id": user_id,'''
new = '''      try:
          existing = (
              supabase_admin
              .table("mod_access")
              .select("id")
              .eq("user_id", user_id)
              .eq("mod_id", req.mod_id)
              .maybe_single()
              .execute()
          )
      except Exception:
          existing = None
      payload = {
          "user_id": user_id,'''
if old in content:
    content = content.replace(old, new)
    open('backend/server.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
