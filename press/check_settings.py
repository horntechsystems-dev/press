import frappe
ps = frappe.get_single("Press Settings")
for f in ["eff_registration_email", "certbot_directory", "webroot_directory", "root_domain", "rsa_key_size", "use_staging_ca", "agent_repository_owner", "bench_configuration"]:
    print(f"{f}: {getattr(ps, f, 'NOT SET')}")
