(function(root){
  function tree(items){
    const paths=new Map();
    for(const item of items)paths.set(item.Path,{item,children:[]});
    for(const item of items){let path=item.Path;while(path!=='/'){path=path.slice(0,path.lastIndexOf('/'))||'/';if(!paths.has(path))paths.set(path,{item:{Path:path,Name:path.split('/').pop()||'全部报表',Type:'Folder',virtual:true},children:[]})}}
    for(const [path,node] of paths){if(path==='/')continue;paths.get(path.slice(0,path.lastIndexOf('/'))||'/').children.push(node)}
    for(const node of paths.values())node.children.sort((a,b)=>(a.item.Type==='Folder'?0:1)-(b.item.Type==='Folder'?0:1)||a.item.Name.localeCompare(b.item.Name));
    return paths.get('/')||{item:{Path:'/',Name:'全部报表',Type:'Folder',virtual:true},children:[]};
  }
  function covered(item,selection,items){return items.find(folder=>folder.Type==='Folder'&&folder.Id!==item.Id&&selection.folderIds.has(folder.Id)&&(folder.Path==='/'||item.Path.startsWith(folder.Path+'/')))}
  const api={tree,covered};if(typeof module!=='undefined')module.exports=api;else root.ResourceTree=api;
})(typeof window==='undefined'?globalThis:window);
