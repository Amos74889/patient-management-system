// Small JS helpers (kept minimal and dependency-free)
document.addEventListener('DOMContentLoaded', function(){
  // Future hooks: toasts, animations, AJAX interactions
  // Example: confirm delete
  document.querySelectorAll('a.btn-danger').forEach(function(btn){
    btn.addEventListener('click', function(e){
      if(!confirm('Are you sure you want to delete this item?')) e.preventDefault();
    });
  });
});
