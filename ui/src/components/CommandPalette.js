import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CommandDialog, CommandInput, CommandList, CommandEmpty,
  CommandGroup, CommandItem, CommandSeparator
} from '@/components/ui/command';
import { Home, Server, GitBranch, Rocket, Clock, FileText, LayoutDashboard } from 'lucide-react';

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen(o => !o);
      }
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, []);

  const go = (path) => {
    navigate(path);
    setOpen(false);
  };

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Search commands..." data-testid="command-palette-input" />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>
        <CommandGroup heading="Navigation">
          <CommandItem onSelect={() => go('/')} data-testid="cmd-home">
            <Home className="mr-2 h-4 w-4" strokeWidth={1.5} /> Home
          </CommandItem>
          <CommandItem onSelect={() => go('/dashboard')} data-testid="cmd-dashboard">
            <LayoutDashboard className="mr-2 h-4 w-4" strokeWidth={1.5} /> Dashboard
          </CommandItem>
          <CommandItem onSelect={() => go('/docs')} data-testid="cmd-docs">
            <FileText className="mr-2 h-4 w-4" strokeWidth={1.5} /> API Docs
          </CommandItem>
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Quick Actions">
          <CommandItem onSelect={() => go('/dashboard')} data-testid="cmd-servers">
            <Server className="mr-2 h-4 w-4" strokeWidth={1.5} /> View Servers
          </CommandItem>
          <CommandItem onSelect={() => go('/dashboard')} data-testid="cmd-graph">
            <GitBranch className="mr-2 h-4 w-4" strokeWidth={1.5} /> Capability Graph
          </CommandItem>
          <CommandItem onSelect={() => go('/dashboard')} data-testid="cmd-pipeline">
            <Rocket className="mr-2 h-4 w-4" strokeWidth={1.5} /> Run Pipeline
          </CommandItem>
          <CommandItem onSelect={() => go('/dashboard')} data-testid="cmd-history">
            <Clock className="mr-2 h-4 w-4" strokeWidth={1.5} /> Pipeline History
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
