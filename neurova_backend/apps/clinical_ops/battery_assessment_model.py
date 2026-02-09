from django.db import models 
 
 
class Assessment(models.Model): 
    test_code = models.CharField(max_length=64, unique=True) 
    title = models.CharField(max_length=255) 
    version = models.CharField(max_length=16, default="1.0") 
    description = models.TextField(blank=True) 
 
    questions_json = models.JSONField() 
    is_active = models.BooleanField(default=True) 
 
    def __str__(self): 
        return self.test_code 
 
 
class Battery(models.Model): 
    battery_code = models.CharField(max_length=64, unique=True) 
    name = models.CharField(max_length=255) 
    version = models.CharField(max_length=16, default="1.0") 
    screening_label = models.CharField(max_length=255) 
 
    signoff_required = models.BooleanField(default=False) 
    is_active = models.BooleanField(default=True) 
 
    def __str__(self): 
        return self.battery_code 
 
 
class BatteryAssessment(models.Model): 
    battery = models.ForeignKey( 
        Battery, 
        on_delete=models.CASCADE, 
        related_name="battery_tests" 
    ) 
    assessment = models.ForeignKey( 
        Assessment, 
        on_delete=models.CASCADE, 
        related_name="assessment_batteries" 
    ) 
    display_order = models.PositiveIntegerField() 
 
    class Meta: 
        unique_together = ("battery", "assessment") 
        ordering = ["display_order"] 
 
    def __str__(self): 
        return f"{self.battery.battery_code} → {self.assessment.test_code}"