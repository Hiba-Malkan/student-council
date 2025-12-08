from django.db import models
from accounts.models import User


class Project(models.Model):
    """Projects and purchases (e.g., Teacher's Day, Senior Jackets)"""
    PROJECT_TYPES = [
        ('EVENT', 'Event'),
        ('PURCHASE', 'Purchase'),
        ('INITIATIVE', 'Initiative'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPES)
    
    # Budget
    estimated_budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Timeline
    proposal_date = models.DateField(auto_now_add=True)
    deadline = models.DateField()
    completion_date = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # People
    proposed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='projects_proposed'
    )
    assigned_to = models.ManyToManyField(User, related_name='projects_assigned', blank=True)
    
    # Approval workflow
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['deadline', '-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class ProjectAttachment(models.Model):
    """Attachments for projects (designs, documents, etc.)"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='attachments')
    
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='projects/attachments/')
    file_type = models.CharField(max_length=50, blank=True)  # e.g., "Design", "Document", "Budget"
    
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='project_attachments_uploaded'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.project.title}"


class ProjectMilestone(models.Model):
    """Milestones for projects"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='project_milestones'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['due_date']
    
    def __str__(self):
        return f"{self.title} - {self.project.title}"


class ProjectUpdate(models.Model):
    """Updates and progress reports for projects"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='updates')
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    posted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='project_updates_posted'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.project.title}"


class Purchase(models.Model):
    """Individual purchase items within a project"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='purchases')
    
    item_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    vendor = models.CharField(max_length=200, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ORDERED', 'Ordered'),
        ('RECEIVED', 'Received'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    receipt = models.FileField(upload_to='projects/receipts/', null=True, blank=True)
    
    purchased_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchases_made'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.item_name} - {self.project.title}"
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)