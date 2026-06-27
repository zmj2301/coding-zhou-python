# 模型检查点管理
import os
import torch


class CheckpointManager:
    """模型检查点管理器"""
    
    def __init__(self, save_dir='models', max_checkpoints=5):
        self.save_dir = save_dir
        self.max_checkpoints = max_checkpoints
        
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
    
    def save(self, model, optimizer, epoch, loss, filename=None, 
             is_best=False, extra_info=None):
        """保存检查点"""
        if filename is None:
            filename = f"checkpoint_epoch{epoch}.pth"
        
        filepath = os.path.join(self.save_dir, filename)
        
        save_data = {
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict() if optimizer else None,
            'loss': loss
        }
        
        if extra_info:
            save_data.update(extra_info)
        
        torch.save(save_data, filepath)
        print(f"检查点已保存: {filepath}")
        
        # 如果是最佳模型，保存副本
        if is_best:
            best_path = os.path.join(self.save_dir, 'best_model.pth')
            torch.save(save_data, best_path)
            print(f"最佳模型已保存: {best_path}")
        
        # 清理旧检查点
        self._cleanup_old_checkpoints()
    
    def load(self, filepath, model, optimizer=None):
        """加载检查点"""
        if not os.path.exists(filepath):
            print(f"检查点不存在: {filepath}")
            return None
        
        checkpoint = torch.load(filepath, map_location='cpu')
        
        model.load_state_dict(checkpoint['model_state_dict'])
        
        if optimizer and 'optimizer_state_dict' in checkpoint:
            optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        
        print(f"检查点已加载: {filepath} (Epoch: {checkpoint['epoch']})")
        return checkpoint
    
    def load_best(self, model, optimizer=None):
        """加载最佳模型"""
        best_path = os.path.join(self.save_dir, 'best_model.pth')
        return self.load(best_path, model, optimizer)
    
    def get_latest_checkpoint(self):
        """获取最新检查点路径"""
        checkpoints = []
        for f in os.listdir(self.save_dir):
            if f.startswith('checkpoint_') and f.endswith('.pth'):
                checkpoints.append(os.path.join(self.save_dir, f))
        
        if not checkpoints:
            return None
        
        checkpoints.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return checkpoints[0]
    
    def _cleanup_old_checkpoints(self):
        """清理旧检查点"""
        checkpoints = []
        for f in os.listdir(self.save_dir):
            if f.startswith('checkpoint_') and f.endswith('.pth'):
                path = os.path.join(self.save_dir, f)
                checkpoints.append((path, os.path.getmtime(path)))
        
        if len(checkpoints) > self.max_checkpoints:
            checkpoints.sort(key=lambda x: x[1])
            for i in range(len(checkpoints) - self.max_checkpoints):
                os.remove(checkpoints[i][0])
                print(f"已删除旧检查点: {checkpoints[i][0]}")
