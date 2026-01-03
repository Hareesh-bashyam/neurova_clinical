def report_upload_path(instance, filename):
    return f"org/{instance.organization.code}/reports/{instance.id}/{filename}"
